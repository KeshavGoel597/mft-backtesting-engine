"""
Portfolio — tracks positions, computes PnL.

Responsibilities:
  - Maintain open positions.
  - Apply trades (open / close positions).
  - Mark-to-market all positions each second.
  - Track realized PnL.
  - Record PnL snapshots for equity curve.
"""

from __future__ import annotations

import datetime as dt
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .market_state import MarketState
from .models import Instrument, PnLSnapshot, Position, Side, Trade

logger = logging.getLogger(__name__)


class Portfolio:
    """
    Tracks all positions and computes PnL.

    Positions are keyed by Instrument.
    Max position per instrument = 1 (as per assignment).
    """

    def __init__(self) -> None:
        self._positions: Dict[Instrument, Position] = {}
        self._realized_pnl: float = 0.0
        self._trade_log: List[Trade] = []
        self._pnl_snapshots: List[PnLSnapshot] = []

    @property
    def positions(self) -> Dict[Instrument, Position]:
        return dict(self._positions)

    @property
    def realized_pnl(self) -> float:
        return self._realized_pnl

    @property
    def unrealized_pnl(self) -> float:
        return sum(p.unrealized_pnl for p in self._positions.values())

    @property
    def total_pnl(self) -> float:
        return self._realized_pnl + self.unrealized_pnl

    @property
    def trade_log(self) -> List[Trade]:
        return list(self._trade_log)

    @property
    def pnl_snapshots(self) -> List[PnLSnapshot]:
        return list(self._pnl_snapshots)

    @property
    def num_positions(self) -> int:
        return len(self._positions)

    def apply_trade(self, trade: Trade) -> None:
        """
        Apply a trade to the portfolio.

        BUY → open a new position (or add to existing — but max=1 per assignment).
        SELL → close an existing position, realize PnL.
        """
        self._trade_log.append(trade)

        if trade.side == Side.BUY:
            if trade.instrument in self._positions:
                logger.warning(
                    "Already have position in %s, ignoring BUY",
                    trade.instrument,
                )
                return

            self._positions[trade.instrument] = Position(
                instrument=trade.instrument,
                side=Side.BUY,
                quantity=trade.quantity,
                entry_price=trade.price,
                entry_time=trade.timestamp,
                current_price=trade.price,
                last_update=trade.timestamp,
            )
            logger.debug(
                "Opened position: BUY %s @ %.2f",
                trade.instrument, trade.price,
            )

        elif trade.side == Side.SELL:
            pos = self._positions.pop(trade.instrument, None)
            if pos is None:
                logger.warning(
                    "No position to close for %s, ignoring SELL",
                    trade.instrument,
                )
                return

            # Realize PnL: we bought at entry_price, selling at trade.price
            pnl = (trade.price - pos.entry_price) * pos.quantity
            self._realized_pnl += pnl
            logger.debug(
                "Closed position: SELL %s @ %.2f (entry=%.2f, pnl=%.2f)",
                trade.instrument, trade.price, pos.entry_price, pnl,
            )

    def mark_to_market(
        self, market_state: MarketState, timestamp: dt.datetime
    ) -> None:
        """
        Update all position prices from current market state
        and record a PnL snapshot.
        """
        for instrument, position in self._positions.items():
            price = market_state.get_option_price(instrument)
            if price is not None:
                position.mark_to_market(price, timestamp)

        snapshot = PnLSnapshot(
            timestamp=timestamp,
            unrealized_pnl=self.unrealized_pnl,
            realized_pnl=self._realized_pnl,
            total_pnl=self.total_pnl,
            num_positions=self.num_positions,
        )
        self._pnl_snapshots.append(snapshot)

    def reset_for_new_day(self) -> None:
        """
        Reset positions for a new trading day.
        Keeps accumulated realized PnL and trade log.
        """
        if self._positions:
            logger.warning(
                "Resetting portfolio with %d open positions!",
                len(self._positions),
            )
        self._positions.clear()

    def full_reset(self) -> None:
        """Complete reset for a fresh simulation."""
        self._positions.clear()
        self._realized_pnl = 0.0
        self._trade_log.clear()
        self._pnl_snapshots.clear()
