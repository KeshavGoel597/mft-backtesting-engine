# MFT Backtesting Engine

Event-driven backtesting framework for the MFT internship assignment.

The project simulates an ATM straddle strategy on `NIFTY` and `BANKNIFTY`, replays tick data second by second, and produces trade logs, daily summaries, PnL snapshots, and charts.

## Highlights

- Clear separation of concerns across replay, market state, strategy, execution, portfolio, analytics, and plotting
- Point-in-time state updates to avoid lookahead bias
- Atomic multi-leg execution for straddle entry and exit
- Configurable slippage, fees, and stale-quote rejection
- CSV and chart outputs suitable for analysis and portfolio review

## Repository Layout

- `run_backtest.py`: command-line entry point
- `backtester/`: core framework modules
- `tests/`: self-contained automated tests and fixtures
- `output/`: example reports generated from a prior run
- `llm_context/`: architecture notes, assumptions, and assignment context

## Quick Start

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the test suite:

```bash
pytest -q
```

Run the backtest:

```bash
python3 run_backtest.py
```

Useful runtime flags:

```bash
python3 run_backtest.py \
  --slippage-bps 5 \
  --fee-per-order 2.0 \
  --max-quote-age-seconds 2 \
  --skip-plots
```

## Data Expectations

The full assignment dataset is not bundled in the repository. `run_backtest.py` expects a local `allData/` directory with the original day folders and CSV files.

The automated tests do not depend on that external dataset. They generate a synthetic fixture tree that mirrors the expected file structure, so `pytest` should pass on a clean checkout.

## Generated Outputs

Running the backtest writes reports to `output/`:

- `trade_log.csv`
- `daily_summary.csv`
- `pnl_snapshots.csv`
- `equity_curve.png`
- `daily_pnl.png`
- `realized_pnl.png`
- `positions.png`
- `backtest.log`

These files are generated artifacts and can be regenerated at any time.

## Design Notes

Supplementary documentation lives in `documentation/`:

- `assignment.md`: source problem statement
- `assumptions.md`: implementation assumptions
- `architecture.md`: system-level design
- `BACKTEST_FRAMEWORK_SPEC.md`: module-level spec
- `DOMAIN_MODEL.md`: domain model definitions

