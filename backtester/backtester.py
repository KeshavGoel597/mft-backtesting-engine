"""
Backtester — the top-level orchestrator.

Responsibilities:
  - Wire all modules together.
  - Run the simulation day by day.
  - Coordinate: ReplayEngine → Strategy → Execution → Portfolio.
  - Collect results.

This is the only module that knows about all other modules.
"""

from __future__ import annotations

import datetime as dt
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from .data_loader import DayData, discover_trading_days, load_day
from .execution import ExecutionEngine
from .market_state import MarketState
from .models import PnLSnapshot, Trade
from .portfolio import Portfolio
from .replay_engine import ReplayEngine
from .strategy import BaseStrategy

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------

@dataclass
class BacktestResult:
    """Aggregated results from a complete backtest run."""
    trades: List[Trade]
    pnl_snapshots: List[PnLSnapshot]
    daily_summaries: List[DailySummary]
    total_realized_pnl: float
    total_days: int
    total_seconds_simulated: int
    wall_time_seconds: float


@dataclass
class DailySummary:
    """Summary metrics for one trading day."""
    date: dt.date
    nifty_trades: int
    banknifty_trades: int
    nifty_pnl: float
    banknifty_pnl: float
    combined_pnl: float
    wall_time_seconds: float


# ---------------------------------------------------------------------------
# Backtester
# ---------------------------------------------------------------------------

class Backtester:
    """
    Orchestrates the entire backtest simulation.

    Usage:
        strategies = [
            ATMStraddleStrategy("NIFTY"),
            ATMStraddleStrategy("BANKNIFTY"),
        ]
        bt = Backtester(data_root=Path("allData"), strategies=strategies)
        result = bt.run()
    """

    def __init__(
        self,
        data_root: Path,
        strategies: List[BaseStrategy],
        snapshot_interval: int = 1,  # record PnL snapshot every N seconds
    ) -> None:
        self._data_root = data_root
        self._strategies = strategies
        self._snapshot_interval = snapshot_interval

        # Shared state
        self._market_state = MarketState()
        self._execution = ExecutionEngine()
        self._portfolio = Portfolio()

    @property
    def portfolio(self) -> Portfolio:
        return self._portfolio

    def run(self) -> BacktestResult:
        """
        Run the full backtest across all trading days.
        """
        day_dirs = discover_trading_days(self._data_root)
        daily_summaries: List[DailySummary] = []
        total_seconds = 0

        overall_start = time.time()
        logger.info("=" * 60)
        logger.info("BACKTEST START — %d trading days", len(day_dirs))
        logger.info("=" * 60)

        for day_idx, day_dir in enumerate(day_dirs):
            day_start = time.time()

            # Load day data
            logger.info("Loading day %d/%d: %s", day_idx + 1, len(day_dirs), day_dir.name)
            day_data = load_day(day_dir)

            # Run simulation for this day
            day_seconds, day_summary_list = self._run_day(day_data)
            total_seconds += day_seconds
            daily_summaries.extend(day_summary_list)

            day_elapsed = time.time() - day_start
            logger.info(
                "Day %s complete: %d seconds simulated in %.1fs wall time | PnL: %.2f",
                day_data.date, day_seconds, day_elapsed, self._portfolio.total_pnl,
            )

        overall_elapsed = time.time() - overall_start
        logger.info("=" * 60)
        logger.info(
            "BACKTEST COMPLETE — total PnL: %.2f | %d trades | %.1fs",
            self._portfolio.total_pnl,
            len(self._portfolio.trade_log),
            overall_elapsed,
        )
        logger.info("=" * 60)

        return BacktestResult(
            trades=self._portfolio.trade_log,
            pnl_snapshots=self._portfolio.pnl_snapshots,
            daily_summaries=daily_summaries,
            total_realized_pnl=self._portfolio.realized_pnl,
            total_days=len(day_dirs),
            total_seconds_simulated=total_seconds,
            wall_time_seconds=overall_elapsed,
        )

    def _run_day(self, day_data: DayData) -> tuple[int, List[DailySummary]]:
        """
        Simulate one trading day.

        Returns (num_seconds_replayed, list_of_daily_summaries).
        """
        # Reset market state for new day
        self._market_state.clear()
        self._portfolio.reset_for_new_day()

        # Track per-strategy metrics
        strategy_trade_counts: Dict[str, int] = {}
        strategy_start_pnl: Dict[str, float] = {}
        for strat in self._strategies:
            key = getattr(strat, 'underlying', str(strat))
            strategy_trade_counts[key] = 0
            strategy_start_pnl[key] = self._portfolio.get_realized_pnl_by_underlying(key)

        # Replay
        engine = ReplayEngine(day_data, self._market_state)
        second_count = 0
        last_timestamp: Optional[dt.datetime] = None

        for timestamp in engine.replay():
            second_count += 1
            last_timestamp = timestamp

            # Run each strategy
            for strat in self._strategies:
                orders = strat.on_market_update(
                    self._market_state,
                    timestamp,
                    day_data.registry,
                    day_data.date,
                )

                if orders:
                    trades = self._execution.execute(
                        orders, self._market_state, timestamp
                    )
                    for trade in trades:
                        self._portfolio.apply_trade(trade)

                    key = getattr(strat, 'underlying', str(strat))
                    strategy_trade_counts[key] += len(trades)

            # Mark-to-market
            if second_count % self._snapshot_interval == 0:
                self._portfolio.mark_to_market(self._market_state, timestamp)

        # End-of-day: close all positions
        if last_timestamp is not None:
            for strat in self._strategies:
                eod_orders = strat.on_day_end(
                    self._market_state,
                    last_timestamp,
                    day_data.registry,
                    day_data.date,
                )
                if eod_orders:
                    trades = self._execution.execute(
                        eod_orders, self._market_state, last_timestamp
                    )
                    for trade in trades:
                        self._portfolio.apply_trade(trade)

                    key = getattr(strat, 'underlying', str(strat))
                    strategy_trade_counts[key] += len(trades)

            # Final MTM snapshot
            self._portfolio.mark_to_market(self._market_state, last_timestamp)

        # Build daily summaries
        nifty_pnl = self._portfolio.get_realized_pnl_by_underlying("NIFTY") - strategy_start_pnl.get("NIFTY", 0.0)
        banknifty_pnl = self._portfolio.get_realized_pnl_by_underlying("BANKNIFTY") - strategy_start_pnl.get("BANKNIFTY", 0.0)
        
        summary = DailySummary(
            date=day_data.date,
            nifty_trades=strategy_trade_counts.get("NIFTY", 0),
            banknifty_trades=strategy_trade_counts.get("BANKNIFTY", 0),
            nifty_pnl=nifty_pnl,
            banknifty_pnl=banknifty_pnl,
            combined_pnl=nifty_pnl + banknifty_pnl,
            wall_time_seconds=0.0,  # filled by caller
        )
        return second_count, [summary]
