"""
Plots — generates visual outputs from backtest results.

Uses matplotlib for charting.
All plots are saved to the output directory.
"""

from __future__ import annotations

import datetime as dt
import logging
import os
from pathlib import Path
from typing import List, Optional

_MPL_CACHE_DIR = Path(__file__).resolve().parent.parent / ".matplotlib"
_MPL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_MPL_CACHE_DIR))

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
    title: str = "Equity Curve — Cumulative PnL Over Time",
) -> None:
    """Plot cumulative total PnL over the entire backtest, split by underlying."""
    if not snapshots:
        logger.warning("No PnL snapshots to plot")
        return

    timestamps = [s.timestamp for s in snapshots]
    total_pnl = [s.total_pnl for s in snapshots]
    nifty_pnl = [s.nifty_realized + s.nifty_unrealized for s in snapshots]
    banknifty_pnl = [s.banknifty_realized + s.banknifty_unrealized for s in snapshots]

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(timestamps, total_pnl, linewidth=1.5, color="#2196F3", label="Combined PnL")
    ax.plot(timestamps, nifty_pnl, linewidth=0.9, color="#4CAF50", linestyle="--", alpha=0.8, label="NIFTY PnL")
    ax.plot(timestamps, banknifty_pnl, linewidth=0.9, color="#FF9800", linestyle="--", alpha=0.8, label="BANKNIFTY PnL")

    ax.axhline(y=0, color="gray", linewidth=0.5, linestyle="--")
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel("Time")
    ax.set_ylabel("PnL (INR)")
    ax.legend(frameon=True, facecolor="white", edgecolor="none")
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
    """Plot realized PnL (stepwise, split by underlying)."""
    if not snapshots:
        return

    timestamps = [s.timestamp for s in snapshots]
    realized = [s.realized_pnl for s in snapshots]
    nifty_realized = [s.nifty_realized for s in snapshots]
    banknifty_realized = [s.banknifty_realized for s in snapshots]

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(timestamps, realized, linewidth=1.5, color="#FF9800", label="Combined Realized")
    ax.plot(timestamps, nifty_realized, linewidth=0.9, color="#4CAF50", linestyle="--", alpha=0.8, label="NIFTY Realized")
    ax.plot(timestamps, banknifty_realized, linewidth=0.9, color="#00BCD4", linestyle="--", alpha=0.8, label="BANKNIFTY Realized")

    ax.axhline(y=0, color="gray", linewidth=0.5, linestyle="--")
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel("Time")
    ax.set_ylabel("Realized PnL (INR)")
    ax.legend(frameon=True, facecolor="white", edgecolor="none")
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
    title: str = "Daily Realized PnL by Underlying",
) -> None:
    """Bar chart of per-day realized PnL split side-by-side."""
    if not summaries:
        return

    dates = sorted([s.date for s in summaries])
    nifty_pnls = [s.nifty_pnl for s in summaries]
    banknifty_pnls = [s.banknifty_pnl for s in summaries]

    import numpy as np
    x = np.arange(len(dates))
    width = 0.35

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.bar(x - width/2, nifty_pnls, width, label="NIFTY", color="#4CAF50", alpha=0.85)
    ax.bar(x + width/2, banknifty_pnls, width, label="BANKNIFTY", color="#FF9800", alpha=0.85)

    ax.axhline(y=0, color="gray", linewidth=0.5, linestyle="--")
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel("Trading Day")
    ax.set_ylabel("Realized PnL (INR)")
    ax.set_xticks(x)
    ax.set_xticklabels([d.strftime("%m-%d") for d in dates])
    ax.legend(frameon=True, facecolor="white", edgecolor="none")
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
