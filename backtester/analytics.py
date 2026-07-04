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
            "date", "nifty_trades", "banknifty_trades",
            "nifty_realized_pnl", "banknifty_realized_pnl", "combined_realized_pnl",
        ])
        for s in summaries:
            writer.writerow([
                s.date.strftime("%Y-%m-%d"),
                s.nifty_trades,
                s.banknifty_trades,
                f"{s.nifty_pnl:.2f}",
                f"{s.banknifty_pnl:.2f}",
                f"{s.combined_pnl:.2f}",
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
            "nifty_realized", "nifty_unrealized",
            "banknifty_realized", "banknifty_unrealized",
        ])
        for s in snapshots:
            writer.writerow([
                s.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                f"{s.unrealized_pnl:.2f}",
                f"{s.realized_pnl:.2f}",
                f"{s.total_pnl:.2f}",
                s.num_positions,
                f"{s.nifty_realized:.2f}",
                f"{s.nifty_unrealized:.2f}",
                f"{s.banknifty_realized:.2f}",
                f"{s.banknifty_unrealized:.2f}",
            ])
    logger.info("PnL snapshots written to %s (%d rows)", output_path, len(snapshots))


def compute_statistics(trades: List[Trade], snapshots: List[PnLSnapshot], total_days: int) -> dict:
    """Compute advanced performance statistics from trade log and snapshots."""
    stats = {}
    stats["total_days"] = total_days
    stats["total_trades"] = len(trades)
    stats["avg_trades_day"] = len(trades) / total_days if total_days > 0 else 0

    # Drawdown
    max_dd = 0.0
    peak = -99999999.0
    for s in snapshots:
        val = s.total_pnl
        if val > peak:
            peak = val
        dd = peak - val
        if dd > max_dd:
            max_dd = dd
    stats["max_drawdown"] = max_dd

    # Pair trades to get round-trip statistics
    round_trips = []
    buy_trades = {}
    for t in trades:
        if t.side == Side.BUY:
            buy_trades[t.instrument] = t
        elif t.side == Side.SELL:
            buy_t = buy_trades.pop(t.instrument, None)
            if buy_t is not None:
                pnl = (t.price - buy_t.price) * t.quantity
                holding_time = (t.timestamp - buy_t.timestamp).total_seconds()
                round_trips.append((pnl, holding_time))

    if round_trips:
        pnls = [rt[0] for rt in round_trips]
        holding_times = [rt[1] for rt in round_trips]
        winning_trades = [p for p in pnls if p > 0]

        stats["win_rate"] = (len(winning_trades) / len(pnls)) * 100
        stats["largest_win"] = max(pnls)
        stats["largest_loss"] = min(pnls)
        # Convert avg holding time to clean HH:MM:SS format
        avg_seconds = sum(holding_times) / len(holding_times)
        m, s = divmod(int(avg_seconds), 60)
        h, m = divmod(m, 60)
        stats["avg_holding_time"] = f"{h:02d}:{m:02d}:{s:02d}"
    else:
        stats["win_rate"] = 0.0
        stats["largest_win"] = 0.0
        stats["largest_loss"] = 0.0
        stats["avg_holding_time"] = "00:00:00"

    return stats


def print_summary(result: BacktestResult) -> None:
    """Print a human-readable summary to stdout including validation metrics."""
    from .data_loader import validation_report

    stats = compute_statistics(result.trades, result.pnl_snapshots, result.total_days)

    print("\n" + "=" * 75)
    print("                      BACKTEST PERFORMANCE REPORT")
    print("=" * 75)
    print(f"  Trading Days:            {result.total_days}")
    print(f"  Total Trades:            {len(result.trades)} (NIFTY: {sum(s.nifty_trades for s in result.daily_summaries)}, BANKNIFTY: {sum(s.banknifty_trades for s in result.daily_summaries)})")
    print(f"  Avg Trades / Day:        {stats['avg_trades_day']:.1f}")
    print(f"  Avg Option Holding Time: {stats['avg_holding_time']}")
    print(f"  Total Realized PnL:      {result.total_realized_pnl:,.2f} INR")
    print(f"  Max Peak-to-Trough DD:   {stats['max_drawdown']:,.2f} INR")
    print(f"  Win Rate (Round-trips):  {stats['win_rate']:.1f}%")
    print(f"  Largest Winning Trade:   {stats['largest_win']:.2f} INR")
    print(f"  Largest Losing Trade:    {stats['largest_loss']:.2f} INR")
    print(f"  Wall Execution Time:     {result.wall_time_seconds:.1f}s")
    print()

    # Data ingestion validation report
    print("-" * 75)
    print("                      DATA INGESTION VALIDATION")
    print("-" * 75)
    print(f"  Files Scanned:           {validation_report.total_files_scanned}")
    print(f"  Loaded Option Files:     {validation_report.loaded_options}")
    print(f"  Missing Files:           {validation_report.missing_files}")
    print(f"  Duplicate Timestamps:    {validation_report.duplicate_timestamps}")
    print(f"  Malformed Filenames:     {validation_report.malformed_filenames}")
    print(f"  Skipped (Other Asset):   {validation_report.skipped_underlying}")
    print(f"  Non-positive Prices:     {validation_report.non_positive_prices}")
    print(f"  Short / Malformed Rows:  {validation_report.short_rows}")
    print()

    # Daily breakdown
    print("-" * 75)
    print("                            DAILY BREAKDOWN")
    print("-" * 75)
    print(f"{'Date':<12} {'NIFTY Trades':>14} {'BNIFTY Trades':>14} {'NIFTY PnL':>14} {'BNIFTY PnL':>14}")
    print("-" * 75)
    for s in result.daily_summaries:
        print(
            f"{s.date}  {s.nifty_trades:>14d} {s.banknifty_trades:>14d} "
            f"{s.nifty_pnl:>14.2f} {s.banknifty_pnl:>14.2f}"
        )
    print("=" * 75)
