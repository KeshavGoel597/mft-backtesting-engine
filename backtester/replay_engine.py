"""
Replay Engine — replays historical market data chronologically.

Responsibilities:
  - Merge all tick streams (futures + options) into a single chronological stream.
  - Advance second-by-second, updating MarketState.
  - Yield control to the Backtester at each second boundary.
  - No trading logic, no strategy awareness.

Design:
  - Uses a merge-sort approach over pre-sorted tick lists.
  - Groups ticks by second for batch processing.
  - Within one second, ALL ticks are applied to MarketState before
    yielding to the caller — this means strategy sees the latest
    price within that second (consistent with the "last trade" assumption).
"""

from __future__ import annotations

import datetime as dt
import heapq
import logging
from dataclasses import dataclass
from typing import Dict, Iterator, List, Optional, Tuple, Union

from .data_loader import DayData
from .market_state import MarketState
from .models import FuturesTick, Instrument, Tick

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Unified tick wrapper for heap merging
# ---------------------------------------------------------------------------

@dataclass(order=False)
class _TaggedTick:
    """Wrapper to allow heterogeneous ticks in a heap sorted by timestamp."""
    timestamp: dt.datetime
    sequence: int            # tie-breaker for stable sort
    tick: Union[Tick, FuturesTick]

    def __lt__(self, other: _TaggedTick) -> bool:
        if self.timestamp != other.timestamp:
            return self.timestamp < other.timestamp
        return self.sequence < other.sequence


# ---------------------------------------------------------------------------
# Replay Engine
# ---------------------------------------------------------------------------

class ReplayEngine:
    """
    Replays a single trading day's market data chronologically.

    Usage:
        engine = ReplayEngine(day_data, market_state)
        for second_ts in engine.replay():
            # market_state is updated with all ticks up to second_ts
            orders = strategy.on_market_update(market_state, second_ts)
            ...
    """

    def __init__(self, day_data: DayData, market_state: MarketState) -> None:
        self._day_data = day_data
        self._market_state = market_state
        self._total_ticks = 0

    @property
    def total_ticks_replayed(self) -> int:
        return self._total_ticks

    def replay(self) -> Iterator[dt.datetime]:
        """
        Replay all ticks for the day, yielding at each unique second.

        At each yield point, MarketState contains the latest data
        for all instruments up to and including that second.
        """
        merged = self._build_merged_stream()

        current_second: Optional[dt.datetime] = None
        tick_count = 0

        for tagged in merged:
            tick_second = tagged.timestamp.replace(microsecond=0)

            # If we've moved to a new second, yield the previous one
            if current_second is not None and tick_second > current_second:
                yield current_second

            current_second = tick_second

            # Apply tick to market state
            if isinstance(tagged.tick, FuturesTick):
                self._market_state.update_futures_tick(tagged.tick)
            elif isinstance(tagged.tick, Tick):
                self._market_state.update_option_tick(tagged.tick)

            tick_count += 1

        # Yield the final second
        if current_second is not None:
            yield current_second

        self._total_ticks = tick_count
        logger.info(
            "Replay complete for %s: %d ticks processed",
            self._day_data.date, tick_count,
        )

    def _build_merged_stream(self) -> Iterator[_TaggedTick]:
        """
        Merge all tick sources into a single chronologically-ordered stream.

        Uses a heap (priority queue) over iterators for memory efficiency —
        we don't need to hold all ticks in memory simultaneously if the
        source lists are already sorted (which they are, since CSVs are
        chronologically ordered).
        """
        seq = 0
        heap: List[Tuple[_TaggedTick, int, Iterator]] = []

        # Add futures tick streams
        for underlying, ticks in self._day_data.futures_ticks.items():
            if ticks:
                it = iter(ticks)
                first = next(it)
                tagged = _TaggedTick(first.timestamp, seq, first)
                heapq.heappush(heap, (tagged, seq, it))
                seq += 1

        # Add option tick streams
        for instrument, ticks in self._day_data.option_ticks.items():
            if ticks:
                it = iter(ticks)
                first = next(it)
                tagged = _TaggedTick(first.timestamp, seq, first)
                heapq.heappush(heap, (tagged, seq, it))
                seq += 1

        # Merge
        while heap:
            tagged, stream_seq, it = heapq.heappop(heap)
            yield tagged

            try:
                nxt = next(it)
                seq += 1
                next_tagged = _TaggedTick(nxt.timestamp, seq, nxt)
                heapq.heappush(heap, (next_tagged, seq, it))
            except StopIteration:
                pass
