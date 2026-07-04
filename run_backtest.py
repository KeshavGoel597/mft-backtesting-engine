#!/usr/bin/env python3
"""
Main entry point — runs the complete backtest.

Usage:
    python3 run_backtest.py
"""

import logging
import sys
import time
from pathlib import Path

# Project imports
from backtester.backtester import Backtester
from backtester.strategy import ATMStraddleStrategy
from backtester.analytics import (
    write_trade_log,
    write_daily_summary,
    write_pnl_snapshots,
    print_summary,
)
from backtester.plots import generate_all_plots

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATA_ROOT = Path(__file__).parent / "allData"
OUTPUT_DIR = Path(__file__).parent / "output"

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(OUTPUT_DIR / "backtest.log", mode="w"),
    ],
)
logger = logging.getLogger(__name__)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 60)
    logger.info("MFT Backtesting Framework")
    logger.info("Strategy: ATM Straddle on NIFTY + BANKNIFTY")
    logger.info("Data: %s", DATA_ROOT)
    logger.info("=" * 60)

    # Create strategies — one per underlying
    strategies = [
        ATMStraddleStrategy("NIFTY"),
        ATMStraddleStrategy("BANKNIFTY"),
    ]

    # Run backtest
    bt = Backtester(
        data_root=DATA_ROOT,
        strategies=strategies,
        snapshot_interval=1,  # snapshot every second
    )
    result = bt.run()

    # --- Write outputs ---
    write_trade_log(result.trades, OUTPUT_DIR / "trade_log.csv")
    write_daily_summary(result.daily_summaries, OUTPUT_DIR / "daily_summary.csv")
    write_pnl_snapshots(result.pnl_snapshots, OUTPUT_DIR / "pnl_snapshots.csv")

    # --- Print summary ---
    print_summary(result)

    # --- Generate plots ---
    try:
        generate_all_plots(result, OUTPUT_DIR)
    except ImportError as e:
        logger.warning("Could not generate plots (matplotlib missing?): %s", e)
    except Exception as e:
        logger.error("Error generating plots: %s", e, exc_info=True)

    logger.info("All outputs saved to %s", OUTPUT_DIR)


if __name__ == "__main__":
    main()
