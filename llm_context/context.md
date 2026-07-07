Assignment Summary

The assignment is to build a reusable backtesting framework for an options trading strategy using one month of historical NSE market data.

The goal is not to maximize profitability.

The goal is to design a modular, extensible and efficient backtesting framework where different strategies can easily be plugged in.

This is an internship assignment for an MFT startup company.

What is actually being evaluated?

Although the assignment specifies a simple ATM strategy,
the emphasis appears to be on designing a reusable,
modular and extensible backtesting framework.

The strategy is intentionally simple so that the engineering
quality of the framework becomes the primary focus.

Engineering Philosophy

- Separation of concerns
- Extensibility over hardcoding
- Single responsibility
- Domain-driven design
- Avoid premature optimization
- Production-inspired, not production-complete
- Prefer clarity over cleverness

Dataset
allData/

    NSE_20221101/

        Futures (Continuous)/

            NIFTY-I.csv
            BANKNIFTY-I.csv
            ...

        Options/

            NIFTY22110318100CE.csv
            NIFTY22110318100PE.csv
            ...

Each daily folder contains

Futures
Options

Only

NIFTY-I.csv
BANKNIFTY-I.csv

are used.

Ignore

-II
-III
Option filename format
NIFTY22111018100CE.csv

represents

Underlying : NIFTY

Expiry : 221110

Strike : 18100

Type : CE
Strategy

For every trading day

only trade NIFTY
only trade BANKNIFTY
use nearest expiry
every second determine ATM strike
hold
ATM CE

ATM PE

If ATM changes

Sell old CE

Sell old PE

Buy new CE

Buy new PE

At end of day

Close all positions.

Required Outputs

Trade log

Position history

MTM PnL

Realized PnL

Equity curve

Daily summary

Plots

Important observations about dataset

The dataset is tick data.

Not one row per second.

Multiple trades may occur during one second.

Example

09:15:08

1.55

1.50

1.55

Some seconds have no trades.

Therefore the replay engine must account for irregular timestamps.

Important understanding

The strategy uses

Future price

only to determine

ATM strike.

Trading actually occurs in

Option contracts.

The future itself is never traded.