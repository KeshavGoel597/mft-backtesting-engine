Decision 1

Replay engine owns market progression.

Reason

Strategy should remain independent of data source.

--------

Decision 2

MarketState stores latest known prices.

Reason

Allows multiple strategies without replay changes.

--------

Decision 3

Replay engine replays historical data chronologically.

Reason

Mimics live trading.

--------

Decision 4

Execution is separated from Strategy.

Reason

Allows future execution models.

Decision:
Replay Engine is independent of Strategy.

Reason:
Allows multiple strategies to reuse the same replay logic.

------------------------------------------------

Decision:
Strategy never reads CSV files.

Reason:
Keeps trading logic independent from storage format.

------------------------------------------------

Decision:
Execution is separated from Strategy.

Reason:
Allows different execution models later.

------------------------------------------------

Decision:
Portfolio is responsible only for positions and PnL.

Reason:
Single Responsibility Principle.

------------------------------------------------

Decision:
Replay engine updates MarketState.

Reason:
Single source of truth.


Alternatives Considered

Event Bus

Rejected

Reason

Unnecessary complexity.

--------------------------------

Scheduler Layer

Rejected

Reason

Replay loop is sufficient.

--------------------------------

Plugin Loader

Rejected

Reason

Over-engineering for assignment.

--------------------------------

Pandas-centric architecture

Rejected

Reason

Wanted reusable domain model instead.