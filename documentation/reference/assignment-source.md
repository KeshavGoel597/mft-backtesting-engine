# Assignment Source (Archived)

This file preserves the original internship assignment statement used as the input requirement.

## Original Statement

We have one month of data in `allData`.

- `allData/NSE_YYYYMMDD` is one trading day.
- Each day contains `options` and `futures` folders.
- Options file naming encodes underlying, expiry, strike, and option type.
- Futures contains `NIFTY-I.csv`, `NIFTY-II.csv`, `NIFTY-III.csv` (similarly for BANKNIFTY/FINNIFTY); use `-I` only.

Task summary:

1. Build a backtest for a simple strategy.
2. For each day, for NIFTY and BANKNIFTY:
   - trade nearest-expiry options
   - every second select strike closest to futures price
   - buy both CE and PE
   - when ATM strike changes, close old legs and open new legs
   - close all positions at day end
3. Produce mark-to-market PnL and position/reporting outputs.
4. Keep setup flexible so different strategies can be plugged in.
5. Show cumulative plots for PnL and other metrics.
