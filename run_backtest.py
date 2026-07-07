#!/usr/bin/env python3
"""
Main entry point — runs the complete backtest.

Usage (basic):
    python3 run_backtest.py

Usage (full):
    python3 run_backtest.py \\
        --data-root    allData/ \\
        --output-dir   output/ \\
        --log-level    INFO \\
        --slippage-bps 5 \\
        --fee-per-order 2.0 \\
        --max-quote-age-seconds 2 \\
        --snapshot-interval 1 \\
        --skip-plots

Flags:
    --data-root              Path to tick data directory (default: allData/)
    --output-dir             Path for generated outputs (default: output/)
    --log-level              INFO or DEBUG (default: INFO)
    --slippage-bps           Slippage in basis points applied on fill price (default: 0)
    --fee-per-order          Fixed fee per order in INR (default: 0)
    --max-quote-age-seconds  Reject fills if the last quote is older than N seconds (default: none)
    --snapshot-interval      Record a PnL snapshot every N seconds (default: 1)
    --skip-plots             Skip matplotlib chart generation
"""


import argparse
import datetime as dt
import logging
import sys
from pathlib import Path

# Project imports
from backtester.backtester import Backtester
from backtester.execution import ExecutionConfig, ExecutionEngine
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

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the MFT options backtest.")
    parser.add_argument("--data-root", type=Path, default=DATA_ROOT)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--snapshot-interval", type=int, default=1)
    parser.add_argument("--slippage-bps", type=float, default=0.0)
    parser.add_argument("--fee-per-order", type=float, default=0.0)
    parser.add_argument("--max-quote-age-seconds", type=int, default=None)
    parser.add_argument("--log-level", default="INFO")
    parser.add_argument("--skip-plots", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Setup Logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(args.output_dir / "backtest.log", mode="w"),
        ],
    )

    logger.info("=" * 60)
    logger.info("MFT Backtesting Framework")
    logger.info("Strategy: ATM Straddle on NIFTY + BANKNIFTY")
    logger.info("Data: %s", args.data_root)
    logger.info("=" * 60)

    max_quote_age = None
    if args.max_quote_age_seconds is not None:
        max_quote_age = dt.timedelta(seconds=args.max_quote_age_seconds)

    execution_engine = ExecutionEngine(
        ExecutionConfig(
            slippage_bps=args.slippage_bps,
            fee_per_order=args.fee_per_order,
            max_quote_age=max_quote_age,
        )
    )

    # Create strategies — one per underlying
    strategies = [
        ATMStraddleStrategy("NIFTY", max_option_quote_age=max_quote_age),
        ATMStraddleStrategy("BANKNIFTY", max_option_quote_age=max_quote_age),
    ]

    # Run backtest
    bt = Backtester(
        data_root=args.data_root,
        strategies=strategies,
        snapshot_interval=args.snapshot_interval,
        execution_engine=execution_engine,
    )
    result = bt.run()

    # --- Write outputs ---
    write_trade_log(result.trades, args.output_dir / "trade_log.csv")
    write_daily_summary(result.daily_summaries, args.output_dir / "daily_summary.csv")
    write_pnl_snapshots(result.pnl_snapshots, args.output_dir / "pnl_snapshots.csv")

    # --- Print summary ---
    print_summary(result)

    # --- Generate plots ---
    if not args.skip_plots:
        try:
            generate_all_plots(result, args.output_dir)
        except ImportError as e:
            logger.warning("Could not generate plots (matplotlib missing?): %s", e)
        except Exception as e:
            logger.error("Error generating plots: %s", e, exc_info=True)

    logger.info("All outputs saved to %s", args.output_dir)


if __name__ == "__main__":
    main()
