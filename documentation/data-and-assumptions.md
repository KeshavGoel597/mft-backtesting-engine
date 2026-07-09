# Data and Assumptions

## Dataset Layout

Expected input root (`allData/`) contains day folders in the form `NSE_YYYYMMDD`.

Each day folder contains:

- `Futures (Continuous)/`
- `Options/`

Only the following futures files are consumed:

- `NIFTY-I.csv`
- `BANKNIFTY-I.csv`

## Option Filename Contract

Pattern:

```text
<UNDERLYING><YYMMDD><STRIKE><CE|PE>.csv
```

Example:

```text
NIFTY22110318100CE.csv
```

## Row Contract

CSV rows are parsed as:

1. Date
2. Time
3. Price
4. Volume
5. Open Interest

## Replay and Timing Semantics

- Data is replayed chronologically across all futures and options streams.
- Strategy evaluation happens once per second boundary.
- When multiple ticks occur in a second, strategy sees the latest state for that second.
- If a symbol has no new tick for a second, the latest known tick remains active in market state.

## Trading Assumptions

- Strategy universe: NIFTY and BANKNIFTY only.
- Nearest expiry at or after trading date is used.
- ATM strike is selected by nearest strike to futures price.
- One lot-equivalent quantity per option leg.
- End-of-day closes all open strategy positions.

## Execution Assumptions

- Fill uses latest option quote in `MarketState`.
- Optional slippage (`--slippage-bps`) adjusts fill price.
- Optional per-order fee (`--fee-per-order`) is applied at trade application.
- Optional max quote age rejects stale fills (`--max-quote-age-seconds`).
- Atomic mode for straddle batches: if any leg is unfillable, whole batch is rejected.

## Data Quality Handling

Ingestion tracks:

- malformed option filenames
- missing expected files
- duplicate timestamps
- non-positive prices
- short or malformed rows

Validation counters are reported in the backtest summary output.
