"""
Strategy — produces Orders based on MarketState.

Responsibilities:
  - Observe market state (never modify it).
  - Decide what to buy/sell.
  - Produce Order objects.
  - No execution, no portfolio awareness.

The BaseStrategy defines the interface.
ATMStraddleStrategy implements the assignment's simple strategy.
"""

from __future__ import annotations

import datetime as dt
import logging
from abc import ABC, abstractmethod
from typing import List, Optional

from .data_loader import InstrumentRegistry
from .instrument_selector import ATMSelector, InstrumentSelector
from .market_state import MarketState
from .models import Instrument, OptionType, Order, Side, Trade

logger = logging.getLogger(__name__)


class BaseStrategy(ABC):
    """
    Abstract base for all trading strategies.

    The Backtester calls on_market_update() at each second.
    The strategy returns a list of Orders (may be empty).
    """

    @abstractmethod
    def on_market_update(
        self,
        market_state: MarketState,
        timestamp: dt.datetime,
        registry: InstrumentRegistry,
        trading_date: dt.date,
    ) -> List[Order]:
        """
        Called once per second by the Backtester.

        Returns a list of orders to execute.
        """
        ...

    @abstractmethod
    def on_day_end(
        self,
        market_state: MarketState,
        timestamp: dt.datetime,
        registry: InstrumentRegistry,
        trading_date: dt.date,
    ) -> List[Order]:
        """
        Called at end of trading day to close all positions.
        """
        ...

    @abstractmethod
    def on_trades(self, trades: List[Trade], timestamp: dt.datetime) -> None:
        """Receive fill confirmations for the strategy's own orders."""
        ...

    @abstractmethod
    def reset_for_new_day(self) -> None:
        """Reset any in-memory day state before a new session starts."""
        ...


class ATMStraddleStrategy(BaseStrategy):
    """
    Simple ATM Straddle strategy:

    1. At each second, determine the ATM strike from the futures price.
    2. If no position held → buy ATM CE + ATM PE.
    3. If ATM strike has changed → sell old CE+PE, buy new CE+PE.
    4. At end of day → sell all.
    """

    def __init__(
        self,
        underlying: str,
        max_option_quote_age: Optional[dt.timedelta] = None,
    ) -> None:
        self.underlying = underlying
        self._selector: InstrumentSelector = ATMSelector()
        self._max_option_quote_age = max_option_quote_age

        # Current held instruments (None if no position)
        self._current_ce: Optional[Instrument] = None
        self._current_pe: Optional[Instrument] = None
        self._current_strike: Optional[int] = None

    def on_market_update(
        self,
        market_state: MarketState,
        timestamp: dt.datetime,
        registry: InstrumentRegistry,
        trading_date: dt.date,
    ) -> List[Order]:
        orders: List[Order] = []

        # Determine current ATM strike
        new_strike = self._selector.select_strike(
            self.underlying, market_state, registry, trading_date
        )
        if new_strike is None:
            return orders

        # If strike hasn't changed and we already have positions, do nothing
        if new_strike == self._current_strike and self._current_ce is not None:
            return orders

        # Get the instruments for the new strike
        new_ce, new_pe = self._selector.get_instruments(
            self.underlying, new_strike, registry, trading_date
        )

        if new_ce is None or new_pe is None:
            # Can't form a full straddle — skip
            logger.debug(
                "%s: Cannot form straddle at strike %d (CE=%s, PE=%s)",
                timestamp, new_strike, new_ce, new_pe,
            )
            return orders

        # Enforce that both CE and PE must have valid prices before we enter or shift
        ce_is_fresh = market_state.has_fresh_option_data(
            new_ce, timestamp, self._max_option_quote_age
        )
        pe_is_fresh = market_state.has_fresh_option_data(
            new_pe, timestamp, self._max_option_quote_age
        )
        if not ce_is_fresh or not pe_is_fresh:
            logger.debug(
                "%s %s: Delaying straddle entry/shift at strike %d: "
                "CE %s fresh=%s, PE %s fresh=%s",
                timestamp, self.underlying, new_strike,
                new_ce.symbol, ce_is_fresh, new_pe.symbol, pe_is_fresh,
            )
            return orders

        # Close existing positions if strike changed
        if self._current_ce is not None:
            orders.append(Order(
                instrument=self._current_ce,
                side=Side.SELL,
                quantity=1,
                timestamp=timestamp,
                reason=f"ATM_SHIFT_{self._current_strike}->{new_strike}",
            ))
        if self._current_pe is not None:
            orders.append(Order(
                instrument=self._current_pe,
                side=Side.SELL,
                quantity=1,
                timestamp=timestamp,
                reason=f"ATM_SHIFT_{self._current_strike}->{new_strike}",
            ))

        # Open new positions
        orders.append(Order(
            instrument=new_ce,
            side=Side.BUY,
            quantity=1,
            timestamp=timestamp,
            reason=f"ATM_ENTER_{new_strike}",
        ))
        orders.append(Order(
            instrument=new_pe,
            side=Side.BUY,
            quantity=1,
            timestamp=timestamp,
            reason=f"ATM_ENTER_{new_strike}",
        ))

        logger.debug(
            "%s %s: ATM strike = %d, orders = %d",
            timestamp, self.underlying, new_strike, len(orders),
        )
        return orders

    def on_day_end(
        self,
        market_state: MarketState,
        timestamp: dt.datetime,
        registry: InstrumentRegistry,
        trading_date: dt.date,
    ) -> List[Order]:
        """Close all positions at end of day."""
        orders: List[Order] = []

        if self._current_ce is not None:
            orders.append(Order(
                instrument=self._current_ce,
                side=Side.SELL,
                quantity=1,
                timestamp=timestamp,
                reason="EOD_CLOSE",
            ))
        if self._current_pe is not None:
            orders.append(Order(
                instrument=self._current_pe,
                side=Side.SELL,
                quantity=1,
                timestamp=timestamp,
                reason="EOD_CLOSE",
            ))

        return orders

    def on_trades(self, trades: List[Trade], timestamp: dt.datetime) -> None:
        if not trades:
            return

        buy_trades = [trade for trade in trades if trade.side == Side.BUY]
        if buy_trades:
            ce = next(
                (trade.instrument for trade in buy_trades if trade.instrument.option_type == OptionType.CE),
                None,
            )
            pe = next(
                (trade.instrument for trade in buy_trades if trade.instrument.option_type == OptionType.PE),
                None,
            )
            if ce is None or pe is None:
                logger.warning("%s %s: incomplete straddle fill state update", timestamp, self.underlying)
                return
            self._current_ce = ce
            self._current_pe = pe
            self._current_strike = ce.strike
            return

        self._current_ce = None
        self._current_pe = None
        self._current_strike = None

    def reset_for_new_day(self) -> None:
        self._current_ce = None
        self._current_pe = None
        self._current_strike = None
