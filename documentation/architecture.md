CSV Loader

↓

Replay Engine

↓

Market State

↓

Strategy

↓

Execution

↓

Portfolio

↓

Analytics

Responsibilities

Data Loader

Reads CSV files.

Parses filenames.

Creates instrument metadata.

Provides tick streams.

Replay Engine

Replays market chronologically.

Maintains MarketState.

Provides current snapshot.

No trading logic.

Market State

Stores latest known information for every instrument.

Strategy reads from here.

Execution reads from here.

Strategy

Receives MarketState.

Produces orders.

Contains no file handling.

Execution

Executes orders using current market prices.

Produces trades.

Portfolio

Maintains

Open positions

Cash

MTM

Realized PnL

Analytics

Produces

Trade log

PnL

Plots

Reports






Replay Engine

Input

Historical market data

Output

Updated MarketState

Dependencies

Data Loader

                 Backtester
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
 ReplayEngine     Strategy     Portfolio
        │             │             ▲
        ▼             │             │
   MarketState     Orders      Execution

imagine

ReplayEngine.

Instead of

string

everywhere,

it sees

Instrument

Much cleaner.

Another one.

Tick.

Most students think

timestamp

price

Enough.

But your CSV has

Price

Volume

Open Interest

Therefore

Tick

should represent

exactly one market update.

ReplayEngine

should replay

Ticks.

Another.

Order.

Order is NOT a Trade.

Huge difference.

Suppose Strategy says

BUY

That's an

Order.

Execution

receives

Order

↓

creates

Trade.

Portfolio

receives

Trade.

Not Order.

This separation is beautiful.

Position

Many students compute

PnL

directly.

I don't think that's correct.

Instead

Portfolio

contains

Position.

Position computes

its own

PnL.

Portfolio simply aggregates.

MarketState

Earlier I thought

MarketState stores prices.

I think that's incomplete.

MarketState stores

latest Tick

for every Instrument.

Much richer.

Now Strategy can ask

Current price?

Current volume?

Current OI?

Already available.
ReplayEngine

Should ReplayEngine know

Portfolio?

No.

Should ReplayEngine know

Strategy?

I'm starting to think

No.

ReplayEngine should simply expose

next()

↓

MarketState

Nothing more.

Backtester

coordinates everything.

This is another change.

Earlier we had

Replay

↓

Strategy

I now think

Replay

↓

Backtester

↓

Strategy

Why?

Because Backtester owns

the simulation.

Replay only owns

historical data.

This is much cleaner.

Suddenly the architecture becomes
                 Backtester
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
 ReplayEngine     Strategy     Portfolio
        │             │             ▲
        ▼             │             │
   MarketState     Orders      Execution

I like this MUCH more.

Another realization.

Analytics

should not observe

Replay.

Analytics

should only observe

Portfolio.

Reason

Analytics doesn't care

how trades happened.

Only the outcome.

I think we finally found the correct architecture.

Notice

Every dependency is one-way.

No cycles.

Huge improvement.

This also tells me

what COMPLETE_PROJECT_CONTEXT.md should actually contain.

Not

Architecture

first.

Instead

Problem

↓

Domain Model

↓

Architecture

↓

Algorithms

↓

Implementation

Exactly how software is designed.