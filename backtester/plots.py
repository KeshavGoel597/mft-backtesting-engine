"""
Plots — generates visual outputs from backtest results.

Uses matplotlib for charting.
All plots are saved to the output directory.
"""

from __future__ import annotations

import datetime as dt
import logging
from pathlib import Path
from typing import List, Optional

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from .backtester import BacktestResult, DailySummary
from .models import PnLSnapshot

logger = logging.getLogger(__name__)

# Style
plt.style.use("seaborn-v0_8-darkgrid")


def plot_equity_curve(
    snapshots: List[PnLSnapshot],
    output_path: Path,
    title: str = "Equity Curve — Total PnL Over Time",
) -> None:
    """Plot cumulative total PnL over the entire backtest."""
    if not snapshots:
        logger.warning("No PnL snapshots to plot")
        return

    timestamps = [s.timestamp for s in snapshots]
    total_pnl = [s.total_pnl for s in snapshots]

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(timestamps, total_pnl, linewidth=0.8, color="#2196F3", alpha=0.9)
    ax.fill_between(
        timestamps, total_pnl, 0,
        where=[p >= 0 for p in total_pnl],
        color="#4CAF50", alpha=0.15, label="Profit",
    )
    ax.fill_between(
        timestamps, total_pnl, 0,
        where=[p < 0 for p in total_pnl],
        color="#F44336", alpha=0.15, label="Loss",
    )
    ax.axhline(y=0, color="gray", linewidth=0.5, linestyle="--")
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel("Time")
    ax.set_ylabel("Total PnL (₹)")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    logger.info("Equity curve saved to %s", output_path)


def plot_realized_pnl(
    snapshots: List[PnLSnapshot],
    output_path: Path,
    title: str = "Realized PnL Over Time",
) -> None:
    """Plot realized PnL (stepwise, increases only on trade closes)."""
    if not snapshots:
        return

    timestamps = [s.timestamp for s in snapshots]
    realized = [s.realized_pnl for s in snapshots]

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(timestamps, realized, linewidth=0.8, color="#FF9800")
    ax.axhline(y=0, color="gray", linewidth=0.5, linestyle="--")
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel("Time")
    ax.set_ylabel("Realized PnL (₹)")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    logger.info("Realized PnL plot saved to %s", output_path)


def plot_daily_pnl_bar(
    summaries: List[DailySummary],
    output_path: Path,
    title: str = "Daily Realized PnL",
) -> None:
    """Bar chart of per-day realized PnL."""
    if not summaries:
        return

    # Aggregate by date (sum across underlyings)
    daily_agg: dict[dt.date, float] = {}
    for s in summaries:
        daily_agg[s.date] = daily_agg.get(s.date, 0.0) + s.realized_pnl

    dates = sorted(daily_agg.keys())
    pnls = [daily_agg[d] for d in dates]
    colors = ["#4CAF50" if p >= 0 else "#F44336" for p in pnls]

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.bar(
        [d.strftime("%m-%d") for d in dates],
        pnls,
        color=colors,
        edgecolor="white",
        linewidth=0.5,
    )
    ax.axhline(y=0, color="gray", linewidth=0.5, linestyle="--")
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel("Trading Day")
    ax.set_ylabel("Realized PnL (₹)")
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    logger.info("Daily PnL bar chart saved to %s", output_path)


def plot_positions_over_time(
    snapshots: List[PnLSnapshot],
    output_path: Path,
    title: str = "Open Positions Over Time",
) -> None:
    """Plot number of open positions over time."""
    if not snapshots:
        return

    timestamps = [s.timestamp for s in snapshots]
    positions = [s.num_positions for s in snapshots]

    fig, ax = plt.subplots(figsize=(14, 4))
    ax.fill_between(timestamps, positions, 0, alpha=0.4, color="#9C27B0")
    ax.plot(timestamps, positions, linewidth=0.5, color="#9C27B0")
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel("Time")
    ax.set_ylabel("# Open Positions")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    logger.info("Positions plot saved to %s", output_path)


def generate_all_plots(result: BacktestResult, output_dir: Path) -> None:
    """Generate all standard plots."""
    output_dir.mkdir(parents=True, exist_ok=True)

    plot_equity_curve(
        result.pnl_snapshots,
        output_dir / "equity_curve.png",
    )
    plot_realized_pnl(
        result.pnl_snapshots,
        output_dir / "realized_pnl.png",
    )
    plot_daily_pnl_bar(
        result.daily_summaries,
        output_dir / "daily_pnl.png",
    )
    plot_positions_over_time(
        result.pnl_snapshots,
        output_dir / "positions.png",
    )
    logger.info("All plots generated in %s", output_dir)
