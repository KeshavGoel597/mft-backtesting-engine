# Domain Model

## Core Entities

### Instrument

Represents one option contract.

Fields:

- `underlying` (for example NIFTY)
- `expiry`
- `strike`
- `option_type` (`CE` or `PE`)
- `symbol` (filename stem)

### Tick

Represents one option market update.

Fields:

- `timestamp`
- `price`
- `volume`
- `open_interest`
- `instrument`

### FuturesTick

Represents one futures market update used for ATM selection.

Fields mirror tick market dimensions for futures.

### Order

Intent from strategy to execution.

Fields include instrument, side, quantity, timestamp, and reason.

### Trade

Execution confirmation produced by execution engine.

Includes executed price, reference price, fees, slippage, and linked order metadata.

### Position

Open exposure in one instrument. Tracks entry and current mark to market state.

### PnLSnapshot

Time-series portfolio snapshot containing:

- realized/unrealized/total PnL
- open position count
- fee totals
- per-underlying PnL splits

## Supporting Aggregates

### MarketState

Point-in-time store of latest known futures and option ticks.

### InstrumentRegistry

Day-level security master built from option filenames. Supports nearest expiry, strikes, and instrument lookups.

### DayData

Container for one day of loaded futures ticks, option ticks, and registry.

### BacktestResult

Top-level output object with trade log, snapshots, daily summaries, and run statistics.

## Invariants

- Strategy emits orders, execution emits trades.
- Portfolio is trade-driven (not order-driven).
- Market state only contains information up to current replay time.
- ATM strategy maintains at most one CE and one PE leg per underlying.
