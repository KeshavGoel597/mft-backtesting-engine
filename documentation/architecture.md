# System Architecture

## Design Principles

- Single responsibility per module
- Unidirectional data/control dependencies
- Point-in-time correctness (no lookahead)
- Strategy and execution decoupling

## Runtime Topology

```text
                    Backtester
                        |
        +---------------+----------------+
        |               |                |
        v               v                v
   ReplayEngine      Strategy         Portfolio
        |               |                ^
        v               |                |
    MarketState       Orders         Execution
```

`Backtester` is the orchestrator. All other components remain focused on their own concerns.

## Control Flow Per Replay Second

1. `ReplayEngine` applies all ticks up to a second boundary into `MarketState`.
2. `Backtester` invokes each strategy with current market state.
3. Strategy returns `Order` objects.
4. `ExecutionEngine` attempts fills and returns `Trade` objects.
5. `Portfolio` applies trades and updates realized state.
6. Portfolio marks to market and records a PnL snapshot (based on configured interval).

## Key Boundaries

- `ReplayEngine` does not know about strategy, execution, or portfolio.
- `Strategy` does not read files and does not mutate market state.
- `ExecutionEngine` does not maintain portfolio state.
- `Portfolio` consumes trades only; it does not process orders.
- `Analytics` consumes result artifacts after simulation, not replay internals.

## Why This Structure Works

- Easy to add strategies by implementing the strategy interface.
- Easy to change execution realism (fees/slippage/stale quote limits) without touching strategy logic.
- Easier testing due to explicit and narrow module contracts.
- Lower regression risk because dependencies are one-way and explicit.

Exactly how software is designed.