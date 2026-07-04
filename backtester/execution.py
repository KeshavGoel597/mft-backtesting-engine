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
from dataclasses import dataclass
from typing import List, Optional

from .market_state import MarketState
from .models import Order, Side, Trade

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ExecutionConfig:
    """Runtime controls for execution realism."""
    slippage_bps: float = 0.0
    fee_per_order: float = 0.0
    max_quote_age: Optional[dt.timedelta] = None


class ExecutionEngine:
    """Fills orders using current market prices."""

    def __init__(self, config: Optional[ExecutionConfig] = None) -> None:
        self._config = config or ExecutionConfig()
        self._trade_counter = 0

    def execute(
        self,
        orders: List[Order],
        market_state: MarketState,
        timestamp: dt.datetime,
        atomic_batch: bool = False,
    ) -> List[Trade]:
        """
        Execute a batch of orders.

        Returns a list of Trade objects for orders that could be filled.
        Orders for instruments with no market data are skipped (logged).
        """
        prepared_trades = []
        rejected_orders: List[Order] = []

        for order in orders:
            tick = market_state.get_option_tick(order.instrument)
            if tick is None:
                logger.warning(
                    "Cannot execute order for %s at %s: no market data",
                    order.instrument, timestamp,
                )
                rejected_orders.append(order)
                continue

            quote_age = timestamp - tick.timestamp
            if self._config.max_quote_age is not None and quote_age > self._config.max_quote_age:
                logger.warning(
                    "Rejecting %s on %s at %s: stale quote age=%ss exceeds limit=%ss",
                    order.side.value,
                    order.instrument,
                    timestamp,
                    int(quote_age.total_seconds()),
                    int(self._config.max_quote_age.total_seconds()),
                )
                rejected_orders.append(order)
                continue

            fill_price = self._apply_slippage(tick.price, order.side)
            prepared_trades.append((order, tick.price, fill_price))

        if atomic_batch and rejected_orders:
            logger.warning(
                "Rejected atomic order batch at %s: %d/%d orders were not fillable",
                timestamp,
                len(rejected_orders),
                len(orders),
            )
            return []

        trades: List[Trade] = []
        for order, reference_price, fill_price in prepared_trades:
            self._trade_counter += 1
            trade = Trade(
                instrument=order.instrument,
                side=order.side,
                quantity=order.quantity,
                price=fill_price,
                timestamp=timestamp,
                order=order,
                trade_id=self._trade_counter,
                reference_price=reference_price,
                fees=self._config.fee_per_order,
                slippage=abs(fill_price - reference_price) * order.quantity,
            )
            trades.append(trade)

            logger.debug(
                "Trade #%d: %s %d x %s @ %.2f ref=%.2f fee=%.2f (%s)",
                trade.trade_id,
                trade.side.value,
                trade.quantity,
                trade.instrument,
                trade.price,
                trade.reference_price,
                trade.fees,
                order.reason,
            )

        return trades

    def _apply_slippage(self, reference_price: float, side: Side) -> float:
        if self._config.slippage_bps == 0:
            return reference_price
        adjustment = self._config.slippage_bps / 10000.0
        if side == Side.BUY:
            return reference_price * (1 + adjustment)
        return reference_price * max(0.0, 1 - adjustment)

    def reset(self) -> None:
        """Reset trade counter for a new simulation."""
        self._trade_counter = 0
