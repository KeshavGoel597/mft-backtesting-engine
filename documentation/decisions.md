# Design Decisions

## Accepted Decisions

### 1. Backtester as Orchestrator

Decision:

`Backtester` coordinates replay, strategy, execution, and portfolio.

Why:

- Keeps orchestration in one place
- Prevents coupling strategy to data replay implementation

### 2. Replay Engine Is Strategy-Agnostic

Decision:

`ReplayEngine` only replays data and updates market state.

Why:

- Reuse across strategies
- Better testability and lower coupling

### 3. Orders and Trades Are Separate Concepts

Decision:

Strategy emits `Order`, execution emits `Trade`.

Why:

- Preserves realistic lifecycle
- Allows explicit rejection and execution policy control

### 4. Atomic Multi-Leg Execution

Decision:

Straddle order batches execute atomically.

Why:

- Avoids half-straddle exposure from partial batch failures

### 5. Explicit Data Validation Reporting

Decision:

Track ingestion anomalies and report them in run summary.

Why:

- Improves trust in simulation outcomes
- Helps diagnose data quality without hidden failures

## Rejected Alternatives

### Event Bus and Scheduler Layers

Rejected as unnecessary complexity for assignment scope.

### Plugin Loader for Strategies

Rejected for current scope; strategy interface already provides extension path.

### Pandas-Centric Core Architecture

Rejected in favor of explicit domain model objects and module boundaries.
