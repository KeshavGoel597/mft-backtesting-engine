# MFT Internship Assignment Submission

This repository contains a modular event-driven backtesting framework for the internship assignment:

- Strategy: ATM straddle on `NIFTY` and `BANKNIFTY`
- Market data: one month of tick-level futures and options CSV data
- Outputs: trade log, daily summary, PnL snapshots, and plots

## Project Structure

- `run_backtest.py`: main entry point
- `backtester/`: framework modules
- `tests/`: automated tests
- `output/`: generated backtest reports and plots
- `llm_context/`: supplementary design notes, assumptions, and assignment context

## How To Run

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the backtest:

```bash
python3 run_backtest.py
```

Run the tests:

```bash
pytest -q
```

## Runtime Options

The runner supports configurable execution realism:

```bash
python3 run_backtest.py \
  --slippage-bps 5 \
  --fee-per-order 2.0 \
  --max-quote-age-seconds 2
```

Useful flags:

- `--skip-plots`
- `--snapshot-interval N`
- `--log-level INFO|DEBUG`
- `--output-dir <path>`

## Key Design Choices

- Strict separation between replay, market state, strategy, execution, portfolio, and analytics
- Point-in-time state updates to avoid lookahead bias
- Atomic multi-leg execution for straddle orders
- Configurable slippage, fees, and stale-quote rejection
- Pre-filtering to nearest-expiry contracts for assignment-aligned performance

## Deliverables Included

The `output/` folder contains pre-generated results from the November 2022 backtest:

| File | Description |
|------|-------------|
| `trade_log.csv` | All 32,692 trades with instrument, price, fees, slippage, and reason |
| `daily_summary.csv` | Per-day NIFTY / BANKNIFTY trade counts and realized PnL |
| `equity_curve.png` | Cumulative PnL curve split by underlying |
| `daily_pnl.png` | Side-by-side daily PnL bar chart |
| `realized_pnl.png` | Stepwise realized PnL over the month |
| `positions.png` | Open position count over time |

> `pnl_snapshots.csv` (second-by-second MTM, ~36MB) and `backtest.log` are excluded from the repo due to size but are generated locally on each run.

## Notes

- Documented assumptions: `llm_context/assumptions.md`
- Original problem statement: `llm_context/assignment.md`
- Architecture and design decisions: `llm_context/architecture.md`, `llm_context/BACKTEST_FRAMEWORK_SPEC.md`
