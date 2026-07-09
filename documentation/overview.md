# Project Overview

## Objective

This project implements an event-driven options backtesting engine for the internship assignment strategy:

- Universe: NIFTY and BANKNIFTY options
- Signal anchor: futures price from `*-I.csv`
- Strategy: continuously hold an ATM CE+PE straddle on nearest expiry
- Rebalance: when ATM strike changes
- End-of-day behavior: close all open positions

The framework is intentionally modular so strategy logic, execution assumptions, and analytics can evolve independently.

## What This Repository Delivers

- Chronological replay of tick data with point-in-time state updates
- Strategy interface and a working ATM straddle implementation
- Atomic multi-leg execution with optional slippage and per-order fees
- Portfolio accounting with realized and unrealized PnL tracking
- Exportable CSV reports and optional plots
- Automated tests for data loading, strategy, and execution edge cases

## Scope Boundaries

Included:

- Deterministic historical simulation on local CSV data
- One quantity per option leg
- Pluggable strategy architecture

Not included:

- Live trading integration
- Level-2 book simulation
- Partial fill simulation
- Advanced risk engine

## Runtime Pipeline

```text
Data Loader -> Replay Engine -> Market State -> Strategy -> Execution -> Portfolio -> Analytics
```

The `Backtester` orchestrates this pipeline and is the single top-level coordinator.
