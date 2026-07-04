"""
Market State — single source of truth for current market prices.

Responsibilities:
  - Store the latest Tick for every option instrument.
  - Store the latest FuturesTick for every underlying.
  - Provide point-in-time queries (no future data leakage).
"""

from __future__ import annotations

import datetime as dt
from typing import Dict, List, Optional, Set

from .models import FuturesTick, Instrument, OptionType, Tick


class MarketState:
    """
    Stores the latest known market data for all instruments.

    Updated by the ReplayEngine on each tick.
    Read by Strategy and Execution Engine.
    """

    def __init__(self) -> None:
        self._option_ticks: Dict[Instrument, Tick] = {}
        self._futures_ticks: Dict[str, FuturesTick] = {}  # underlying → tick
        self._current_time: Optional[dt.datetime] = None

    @property
    def current_time(self) -> Optional[dt.datetime]:
        return self._current_time

    def update_option_tick(self, tick: Tick) -> None:
        """Update the latest option tick for an instrument."""
        self._option_ticks[tick.instrument] = tick
        self._update_time(tick.timestamp)

    def update_futures_tick(self, tick: FuturesTick) -> None:
        """Update the latest futures tick for an underlying."""
        self._futures_ticks[tick.underlying] = tick
        self._update_time(tick.timestamp)

    def _update_time(self, ts: dt.datetime) -> None:
        if self._current_time is None or ts >= self._current_time:
            self._current_time = ts

    # --- Query methods ---

    def get_futures_price(self, underlying: str) -> Optional[float]:
        """Latest futures price for the underlying."""
        tick = self._futures_ticks.get(underlying)
        return tick.price if tick else None

    def get_futures_tick(self, underlying: str) -> Optional[FuturesTick]:
        return self._futures_ticks.get(underlying)

    def get_option_tick(self, instrument: Instrument) -> Optional[Tick]:
        """Latest option tick for a specific instrument."""
        return self._option_ticks.get(instrument)

    def get_option_price(self, instrument: Instrument) -> Optional[float]:
        """Latest option price for a specific instrument."""
        tick = self._option_ticks.get(instrument)
        return tick.price if tick else None

    def has_option_data(self, instrument: Instrument) -> bool:
        return instrument in self._option_ticks

    def all_instruments_with_data(self) -> Set[Instrument]:
        """Return all instruments that have at least one tick."""
        return set(self._option_ticks.keys())

    def clear(self) -> None:
        """Reset state for a new trading day."""
        self._option_ticks.clear()
        self._futures_ticks.clear()
        self._current_time = None

    def __repr__(self) -> str:
        return (
            f"MarketState(time={self._current_time}, "
            f"futures={list(self._futures_ticks.keys())}, "
            f"options={len(self._option_ticks)} instruments)"
        )
