# Operations Guide

## Environment Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run the Backtest

Default run:

```bash
python3 run_backtest.py
```

Example with runtime controls:

```bash
python3 run_backtest.py \
  --data-root allData \
  --output-dir output \
  --slippage-bps 5 \
  --fee-per-order 2.0 \
  --max-quote-age-seconds 2 \
  --snapshot-interval 1
```

Skip plot generation:

```bash
python3 run_backtest.py --skip-plots
```

## CLI Flags

- `--data-root`: path to dataset root
- `--output-dir`: where reports and logs are written
- `--snapshot-interval`: PnL snapshot cadence in seconds
- `--slippage-bps`: slippage applied per fill
- `--fee-per-order`: flat fee charged per filled order
- `--max-quote-age-seconds`: stale quote rejection threshold
- `--log-level`: `INFO` or `DEBUG`
- `--skip-plots`: disable chart generation

## Generated Artifacts

Primary CSV outputs:

- `output/trade_log.csv`
- `output/daily_summary.csv`
- `output/pnl_snapshots.csv`

Additional outputs:

- `output/backtest.log`
- chart images from `backtester/plots.py` when plotting is enabled

## Operational Notes

- Tests use synthetic fixture data and do not require the full assignment dataset.
- Backtest runtime and memory depend on dataset size and snapshot interval.
- If stale-quote filtering is enabled, stricter values may reduce trade count.
