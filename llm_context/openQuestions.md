Project Goal

The project should be treated as

a reusable backtesting framework

not

an implementation of one ATM strategy.

The ATM strategy is merely the first strategy supported by the framework.

Guiding Principles
Separation of concerns.
Extensibility.
Clear module responsibilities.
Minimal coupling.
No premature optimization.
Production-inspired but not over-engineered.
Complete, well-documented implementation preferred over incomplete "production-scale" architecture.


Open Questions and Assumptions
During development, we encountered several unspecified aspects of the assignment. For these, we adopted reasonable assumptions and documented them clearly. These decisions were made because no clarification was available before submission. The most significant open questions were:

Tick replay vs one-second replay.
Exact execution model.
Price selection within one second.
Missing timestamps.
Tie-breaking between strikes.

Then note

No clarification was available before submission.

Reasonable assumptions were adopted.

Things we explicitly decided NOT to do:
We decided NOT to

Build one huge script.

We decided NOT to

Hardcode strategy into replay engine.

We decided NOT to

Make Strategy read CSV files.

We decided NOT to

Over-engineer using

Event bus
Dependency Injection
Observer Pattern
Plugin loaders
Message queues
because they add complexity without helping this assignment.

We decided NOT to

Use pandas DataFrames as the core architecture.

Pandas may be used for loading or plotting, but the framework should be built around domain objects rather than DataFrame operations.