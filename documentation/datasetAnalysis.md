# Dataset Analysis

## Directory Structure

allData/
    NSE_YYYYMMDD/
        Futures (Continuous)/
        Options/

## Futures

Only NIFTY-I.csv and BANKNIFTY-I.csv are used.

-II and -III are ignored.

## Option Filename Format

<Underlying><Expiry><Strike><Type>.csv

Example:
NIFTY22111018100CE.csv

Underlying : NIFTY
Expiry : 221110
Strike : 18100
Type : CE

## CSV Format

Date
Time
Price
Volume
Open Interest

## Observations

- Tick-level data.
- Multiple trades may occur within the same second.
- Missing seconds are common.
- Rows appear to represent executed trades.
- Volume and Open Interest are available.
- Future and option timestamps may not align exactly.