"""
Analytics — generates reports, trade logs, and plots from backtest results.

Responsibilities:
  - Format trade log as a table.
  - Generate daily summary report.
  - Plot cumulative PnL / equity curve.
  - Plot position timeline.
"""

from __future__ import annotations

import csv
import datetime as dt
import logging
from pathlib import Path
from typing import List, Optional

from .backtester import BacktestResult, DailySummary
from .models import PnLSnapshot, Side, Trade

logger = logging.getLogger(__name__)


def write_trade_log(trades: List[Trade], output_path: Path) -> None:
    """Write trade log to CSV."""
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "trade_id", "timestamp", "underlying", "expiry", "strike",
            "option_type", "side", "quantity", "price", "reason",
        ])
        for t in trades:
            writer.writerow([
                t.trade_id,
                t.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                t.instrument.underlying,
                t.instrument.expiry.strftime("%Y-%m-%d"),
                t.instrument.strike,
                t.instrument.option_type.value,
                t.side.value,
                t.quantity,
                f"{t.price:.2f}",
                t.order.reason,
            ])
    logger.info("Trade log written to %s (%d trades)", output_path, len(trades))


def write_daily_summary(
    summaries: List[DailySummary], output_path: Path
) -> None:
    """Write daily summary to CSV."""
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "date", "underlying", "num_trades", "strike_changes",
            "day_realized_pnl", "cumulative_pnl",
        ])
        for s in summaries:
            writer.writerow([
                s.date.strftime("%Y-%m-%d"),
                s.underlying,
                s.num_trades,
                s.num_strike_changes,
                f"{s.realized_pnl:.2f}",
                f"{s.closing_pnl:.2f}",
            ])
    logger.info("Daily summary written to %s", output_path)


def write_pnl_snapshots(
    snapshots: List[PnLSnapshot], output_path: Path
) -> None:
    """Write PnL snapshots to CSV for external analysis."""
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "timestamp", "unrealized_pnl", "realized_pnl",
            "total_pnl", "num_positions",
        ])
        for s in snapshots:
            writer.writerow([
                s.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                f"{s.unrealized_pnl:.2f}",
                f"{s.realized_pnl:.2f}",
                f"{s.total_pnl:.2f}",
                s.num_positions,
            ])
    logger.info("PnL snapshots written to %s (%d rows)", output_path, len(snapshots))


def print_summary(result: BacktestResult) -> None:
    """Print a human-readable summary to stdout."""
    print("\n" + "=" * 70)
    print("BACKTEST RESULTS")
    print("=" * 70)
    print(f"  Trading days:        {result.total_days}")
    print(f"  Total trades:        {len(result.trades)}")
    print(f"  Seconds simulated:   {result.total_seconds_simulated:,}")
    print(f"  Wall time:           {result.wall_time_seconds:.1f}s")
    print(f"  Realized PnL:        {result.total_realized_pnl:,.2f}")
    print()

    # Daily breakdown
    print(f"{'Date':<12} {'Underlying':<12} {'Trades':>8} {'Day PnL':>12} {'Cum PnL':>12}")
    print("-" * 58)
    for s in result.daily_summaries:
        print(
            f"{s.date}  {s.underlying:<12} {s.num_trades:>8} "
            f"{s.realized_pnl:>12.2f} {s.closing_pnl:>12.2f}"
        )
    print("=" * 70)
