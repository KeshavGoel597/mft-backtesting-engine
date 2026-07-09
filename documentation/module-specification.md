# Module Specification

## Runtime Entry Point

### run_backtest.py

Responsibilities:

- Parse CLI flags
- Configure logging
- Create strategy and execution instances
- Run `Backtester`
- Write CSV outputs and generate plots

## Core Engine Modules

### backtester/data_loader.py

Responsibilities:

- Discover trading day folders
- Parse option filenames into `Instrument`
- Load futures/options CSV ticks
- Build `InstrumentRegistry`
- Track ingestion validation counters

### backtester/replay_engine.py

Responsibilities:

- Merge all tick streams chronologically
- Update `MarketState`
- Yield one callback point per second boundary

### backtester/market_state.py

Responsibilities:

- Maintain latest futures/option ticks
- Provide current prices and freshness checks

### backtester/strategy.py

Responsibilities:

- Define strategy interface (`BaseStrategy`)
- Implement assignment strategy (`ATMStraddleStrategy`)
- Produce only `Order` objects

### backtester/execution.py

Responsibilities:

- Validate fillability against market state
- Reject stale quotes when configured
- Support atomic batches for multi-leg orders
- Apply slippage and per-order fee model

### backtester/portfolio.py

Responsibilities:

- Apply trades and maintain positions
- Track realized/unrealized PnL and fees
- Emit `PnLSnapshot` time series

### backtester/backtester.py

Responsibilities:

- Orchestrate day-by-day and second-by-second simulation
- Coordinate replay, strategy calls, execution, and portfolio
- Trigger end-of-day position closure
- Build `BacktestResult`

## Analytics and Reporting

### backtester/analytics.py

Responsibilities:

- Write CSV artifacts (`trade_log`, `daily_summary`, `pnl_snapshots`)
- Compute and print performance and validation statistics

### backtester/plots.py

Responsibilities:

- Generate PnL and position visualization artifacts
