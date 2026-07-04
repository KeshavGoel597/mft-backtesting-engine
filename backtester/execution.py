"""
Execution Engine — fills Orders at current market prices.

Responsibilities:
  - Receive Orders from Strategy.
  - Look up current prices in MarketState.
  - Produce Trade objects.
  - No position tracking (that's Portfolio's job).

Current model: immediate fill at last known price (no slippage).
Future: could add slippage models, partial fills, etc.
"""

from __future__ import annotations

import datetime as dt
import logging
from typing import List

from .market_state import MarketState
from .models import Order, Side, Trade

logger = logging.getLogger(__name__)


class ExecutionEngine:
    """Fills orders using current market prices."""

    def __init__(self) -> None:
        self._trade_counter = 0

    def execute(
        self,
        orders: List[Order],
        market_state: MarketState,
        timestamp: dt.datetime,
    ) -> List[Trade]:
        """
        Execute a batch of orders.

        Returns a list of Trade objects for orders that could be filled.
        Orders for instruments with no market data are skipped (logged).
        """
        trades: List[Trade] = []

        for order in orders:
            price = market_state.get_option_price(order.instrument)

            if price is None:
                logger.warning(
                    "Cannot execute order for %s at %s: no market data",
                    order.instrument, timestamp,
                )
                continue

            self._trade_counter += 1
            trade = Trade(
                instrument=order.instrument,
                side=order.side,
                quantity=order.quantity,
                price=price,
                timestamp=timestamp,
                order=order,
                trade_id=self._trade_counter,
            )
            trades.append(trade)

            logger.debug(
                "Trade #%d: %s %d x %s @ %.2f (%s)",
                trade.trade_id,
                trade.side.value,
                trade.quantity,
                trade.instrument,
                trade.price,
                order.reason,
            )

        return trades

    def reset(self) -> None:
        """Reset trade counter for a new simulation."""
        self._trade_counter = 0
