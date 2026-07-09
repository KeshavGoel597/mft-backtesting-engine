This looks like a well-scoped backtesting assignment. I understand the overall objective, and I also have a few clarifications that I'd ask before implementing it to avoid making incorrect assumptions.

My understanding

For every trading day:

Process only NIFTY and BANKNIFTY.
Use only the nearest expiry options available on that day.
Use NIFTY-I.csv and BANKNIFTY-I.csv from the futures folder as the reference futures price.
At every timestamp (nominally every second):
Find the strike whose strike price is closest to the current futures price.
Hold exactly:
1 ATM Call
1 ATM Put
If the ATM strike changes:
Sell both current positions.
Buy the new ATM CE and PE.
At end of day:
Close any remaining positions.
Produce a backtest with:
Executed trades
Open positions
Realized PnL
Unrealized (MTM) PnL
Equity curve
Performance statistics
Plots

Architecture I'd propose

Rather than writing everything inside one script, I'd make it modular so different strategies can be plugged in later.

project/
│
├── data/
│   └── allData/
│
├── engine/
│   ├── backtester.py
│   ├── portfolio.py
│   ├── order.py
│   ├── trade.py
│   ├── execution.py
│   └── data_loader.py
│
├── strategies/
│   ├── base_strategy.py
│   └── atm_straddle.py
│
├── reports/
│   ├── trades.csv
│   ├── positions.csv
│   ├── pnl.csv
│   └── plots/
│
└── run_backtest.py

Then implementing another strategy later becomes as simple as

class MyStrategy(BaseStrategy):
    def on_market_data(...):
        ...

without touching the backtester.

Metrics I'd generate
Trade Log

|Time|Instrument|Side|Qty|Price|

Position History

|Time|Instrument|Position|Average Price|

MTM Timeline

|Time|Realized|Unrealized|Total|

Daily Summary
Gross PnL
Number of trades
Average holding time
Maximum open positions
Maximum drawdown
Win/Loss statistics (if desired)
Plots
Equity curve
Daily cumulative PnL
Drawdown
Number of open positions over time
Distribution of holding time
Histogram of trade PnL
Clarifications
1. Timestamp synchronization (most important)

The options and futures files may not have identical timestamps.

Suppose

Future:
09:30:01

Option:
09:30:00
09:30:02

Should I

A. use the latest available option price at or before the futures timestamp (most realistic),
B. require exact timestamp matches,
C. interpolate?

I would recommend A.

2. Strike selection

If futures is

18177

and strikes are

18150
18200

Should I choose

18200

because it is closer?

What if

18175

which is exactly halfway?

Should ties always round

upward?
downward?
3. Missing option file

Suppose ATM strike is

18150

but

NIFTY22110318150CE.csv

does not exist.

Should I

skip trading
choose the next closest strike
wait until available
4. Price used

The files contain only

Price

Should this be treated as the executable trade price?

5. Transaction costs

Should I assume

brokerage = 0
slippage = 0
fees = 0

unless specified?

6. Position change

Suppose

ATM = 18100

At next second

still 18100

Do nothing.

Only when ATM changes to

18150

do we

SELL old CE
SELL old PE
BUY new CE
BUY new PE

Correct?

7. Mark-to-market frequency

Should MTM be calculated

every second,
only when market data changes,
only after trades?

I'd normally compute it whenever a new market price arrives.

8. End-of-day

Should positions be closed

at the final available tick,
at 15:30:00,
or at the last timestamp present in the files?
One practical note

I can't directly access the Google Drive file from the link alone in this chat. If you upload the dataset (or even just one day's folder as a ZIP), I can inspect the exact file format and build the framework accordingly, ensuring it matches the data structure precisely. 





Step 1: What is the naive approach?

Suppose one day's Options folder contains:

Options/
    NIFTY22111018000CE.csv
    NIFTY22111018000PE.csv
    NIFTY22111018050CE.csv
    NIFTY22111018050PE.csv
    ...
    NIFTY22111019000CE.csv
    NIFTY22111019000PE.csv

    BANKNIFTY22111042000CE.csv
    BANKNIFTY22111042000PE.csv
    ...

There could easily be 500–3000 CSV files.

Now imagine it's

09:15:00
Future = 18118

You need

18100 CE
18100 PE
Bad idea

Every second:

Search entire folder

↓

Find correct file

↓

Open CSV

↓

Read line

↓

Close CSV

Now imagine

6 hours of trading.

Approximately

6 × 60 × 60 = 21,600 seconds

Searching thousands of files

21,600 times

is very slow.

Step 2: Think like a software engineer

Ask yourself:

Do filenames change during the day?

No.

The files remain exactly the same.

Therefore,

instead of repeatedly searching,

search once.

Step 3: Build an index

When your program starts,

scan the Options folder only once.

For every filename,

extract

Underlying

Expiry

Strike

CE/PE

Example

NIFTY22111018100CE.csv

becomes

Underlying = NIFTY

Expiry = 221110

Strike = 18100

Type = CE

Store it.

Maybe something like

map<
    string,
    string
> fileMap;

where

Key

NIFTY_221110_18100_CE

Value

path/to/file.csv

Now finding a file becomes

O(log n)

instead of searching thousands of filenames.

Step 4: But opening CSVs is also expensive

Suppose

at

09:15

you need

18100 CE

If every second you

Open CSV

↓

Read one row

↓

Close CSV

that is also slow.

Better idea:

Read each CSV only once.

Store its data in memory.

Example

struct Tick
{
    string time;
    double price;
    int volume;
    int oi;
};

Then

unordered_map<
    string,
    vector<Tick>
> optionData;

Now

optionData["NIFTY22111018100CE"]

contains

09:15

09:15:01

09:15:02

...

already loaded.

No disk access later.

Step 5: But there are thousands of CSVs!

Exactly.

Should you load every CSV?

Maybe not.

Let's think.

The strategy says

Only nearest expiry.

Suppose today's date

10 Nov

Available expiries

10 Nov

17 Nov

24 Nov

You only need

10 Nov

Immediately,

you can ignore

17 Nov

24 Nov

Already,

maybe

70% of files disappear.

Then

only

NIFTY

and

BANKNIFTY

are needed.

Ignore

FINNIFTY

More files removed.

Now memory usage becomes reasonable.

Step 6: How do we know which strike to use?

Future file

09:15
18118

Available strikes

18000

18050

18100

18150

18200

Need nearest.

Instead of scanning every strike,

store

vector<int> strikes;

sorted.

Example

18000

18050

18100

18150

18200

Now

binary search.

Future

18118

Find nearest.

Very fast.

Step 7: Time synchronization

This is the next challenge.

Future file

09:15:00

09:15:01

09:15:02

Option file

09:15:00

09:15:01

09:15:02

Hopefully timestamps match.

If they don't,

you have to decide

latest available price

or

exact match

depending on assignment assumptions.

This is one of the first things I'd verify by opening a few sample files.

Step 8: Position Manager

You should avoid scattering variables like

currentCE

currentPE

entryPrice

exitPrice

Instead,

make one class.

Portfolio

It knows

Currently holding

↓

Entry price

↓

Current MTM

↓

Realized PnL

Then the strategy simply says

Portfolio.buy()

Portfolio.sell()
Step 9: Separate strategy from engine

This is the "flexible setup" your assignment mentions.

Notice this sentence:

Think out of the box on how you can make this a flexible setup where different strategies can be easily plugged in.

That is a big hint.

Don't write

if strike changes

buy

sell

inside the engine.

Instead

Backtester

↓

calls

↓

Strategy

↓

returns

BUY

SELL

HOLD

Tomorrow

you can replace

ATM Strategy

with

Moving Average Strategy

without changing the backtester.

The architecture I'd recommend
run_backtest.cpp
        │
        ▼
DataLoader
        │
        ▼
MarketData
        │
        ▼
Backtester
        │
        ├────────► Strategy
        │
        ├────────► Portfolio
        │
        ├────────► Execution
        │
        ▼
Reports

Each module has a single responsibility:

DataLoader: Reads CSV files and organizes them in memory.
Strategy: Decides what to buy, sell, or hold based on the current market data.
Execution: Simulates trades at the current market price.
Portfolio: Tracks open positions, realized PnL, and mark-to-market (MTM).
Backtester: Drives the simulation by feeding market data to the strategy and coordinating the other components.
Reports: Produces trade logs, PnL tables, and plots.
If I were implementing this

I would do it in four stages instead of trying to solve everything at once:

Data loading: Parse the folder structure, filenames, and CSVs. Build efficient indexes for options by underlying, expiry, strike, and type.
Replay engine: Iterate through one day's futures data chronologically and make sure you can retrieve the correct option prices at each timestamp.
Trading logic: Implement the simple ATM strategy—buy the nearest-expiry ATM CE and PE, switch when the nearest strike changes, and close positions at the end of the day.
Reporting: Compute realized PnL, MTM over time, trade history, and generate summary plots.
One thing I would verify before writing any code

Since you mentioned the Google Drive dataset, the very first thing I'd inspect is the actual format of one futures CSV and one options CSV.

Specifically, I'd answer questions like:

Are the timestamps exactly one second apart?
Do the futures and options files use identical timestamps?
Are there missing seconds?
Is the Price column the execution price?
Are the rows already sorted by time?

Those details determine how the replay engine should be implemented. Once we know the exact CSV format, the rest of the design becomes much more straightforward.




That changes things significantly. If this is for an HFT/quant trading company rather than a college assignment, then you should not make assumptions just because they make the implementation easier. In quantitative trading, assumptions about market data can completely change the backtest results.

Based on everything you've shown, here's how I would approach it.

First: I would not start coding.

I would first write down the ambiguities and get them clarified. This is exactly what a quantitative developer or quantitative researcher would do.

Here are the questions I would send.

1. The biggest ambiguity: "At every 1 second"

The specification says:

At every 1 sec, select the strike closest to the futures price.

However, the provided data is tick-by-tick, with multiple trades occurring within the same second and some seconds having no trades.

For example:

09:15:00
09:15:00
09:15:00
09:15:00
09:15:01
09:15:02
09:15:04
Clarification

Should the strategy

aggregate all ticks into one observation per second (e.g. use the last traded price within that second),
or process every market tick while evaluating the strategy once every second,
or replay every tick?

This is the single most important question.

2. Execution price

Suppose

09:15:08

1.55
1.50
1.55

Which price should be used if the strategy decides to buy at

09:15:08

Should execution occur at

first trade
last trade
VWAP
average
another convention?
3. Timestamp synchronization

Suppose

Future

09:15:08

Option

09:15:07

09:15:11

No exact timestamp exists.

Should execution use

latest available price
next available price
nearest price

This is another major design decision.

4. Strike rounding

Suppose

Future

18125

Available strikes

18100

18150

Equal distance.

Should ties round

upward
downward
5. Missing instruments

Suppose ATM strike becomes

18150

but

18150 PE

is missing.

Should we

skip trade
use nearest strike
hold previous position
6. Liquidity

Should we ignore

Volume

and assume infinite liquidity,

or

should we check whether enough traded quantity exists?

7. Slippage

Should execution be assumed

exactly at trade price

or

should we model slippage?

8. Transaction costs

Brokerage

Exchange fees

STT

GST

Ignored?

9. Market close

Close at

last available tick
official close time
something else
10. Position sizing

The assignment says

Maximum position = 1

Does this mean

1 contract

or

1 lot

For NIFTY these are different.

Now let's talk architecture.

This is the interesting part.

If this were a college assignment

One script.

Done.

If this were production software

I'd never build it that way.

Instead I'd separate five completely independent components.

1. Data Layer

Responsible only for reading files.

Never contains trading logic.

CSV

↓

Tick objects

↓

Market feed
2. Replay Engine

This is the heart.

Think of it like a stock exchange replaying an old trading day.

Tick

↓

Update market

↓

Notify strategy

No strategy code here.

3. Strategy

Receives

Current Market

Returns

BUY

SELL

HOLD

Nothing else.

4. Execution Engine

Receives

BUY

Determines

Execution price

↓

Trade
5. Portfolio

Keeps

Open positions

Realized PnL

Unrealized PnL

Cash

Equity

Notice

None of these classes know about each other internally.

Only the Backtester coordinates them.

The optimization challenge

You mentioned

highly optimized deployable framework

This changes everything.

The bottleneck is not the strategy.

It's the data.

Suppose

One month

contains

3000 option files/day

×

22 days

=

66000 CSVs

Opening

66000 CSVs

every run

is expensive.

I'd probably preprocess.

Day 1

CSV

↓

Binary format

↓

Index

Then every future run

loads

binary.

10-100× faster.

Another optimization

Instead of

unordered_map<string, ...>

everywhere,

I'd assign integer IDs.

Example

0 -> NIFTY22111018100CE

1 -> NIFTY22111018100PE

2 -> NIFTY22111018150CE

Then

market data becomes

vector<Tick>

instead of hash lookups.

That's much faster.

Another optimization

Don't search strikes repeatedly.

Maintain

sorted strikes

↓

binary search

Every strike lookup becomes

O(log n)

instead of

O(n)
Another optimization

Event-driven.

Never loop

every second

Instead

Next tick

↓

Update only changed instrument

Millions fewer operations.

My biggest concern with the assignment

The assignment repeatedly says

"At every 1 second"

but the dataset is clearly tick-level.

Those are two different datasets.

A professional backtester must know which one it's simulating.

So before writing even a single line of code, I would get that point clarified.

I think we can do something much better

Since this is for an HFT company, I'd be happy to help you build something closer to what firms actually use rather than a one-off assignment.

We can design it like a mini Zipline/Backtrader:

a generic event-driven replay engine,
pluggable strategies,
efficient market-data indexing,
execution and portfolio modules,
analytics and reporting,
and a clean separation so that adding a new strategy requires only implementing a small strategy interface.

That would not only solve this assignment but also be a strong piece of engineering to discuss in interviews or use as a foundation for future quantitative research.


I think that's the right way to approach this, and I'll do exactly that. If at any point I think we're heading down a suboptimal path, I'll stop us and explain why before proceeding.

Also, I'm going to be a bit stricter than usual because this is for an MFT internship. I'll optimize for what would impress an experienced engineer reviewing your code, not just for getting the assignment done.

Step 0: Let's understand what they're really asking

The assignment looks like this:

Build a backtester.

But that's not actually what they're are testing.

I think they're testing four things.

1. Software Architecture ⭐⭐⭐⭐⭐

This is probably the biggest one.

Notice this sentence:

Think out of the box on how you can make this a flexible setup where different strategies can be easily plugged in.

That is not a casual sentence.

That's the entire assignment.

2. Data Engineering ⭐⭐⭐⭐⭐

The data is messy.

Thousands of files.

Millions of rows.

Can you organize it?

3. Clean Code ⭐⭐⭐⭐☆

Can another engineer understand your code?

4. Basic Trading Logic ⭐⭐☆☆☆

The strategy itself is intentionally simple.

Therefore...

I actually want to change one thing I suggested earlier.

Earlier I said

Write ASSUMPTIONS.md

Now I think

Don't.

Instead,

put the assumptions in the README.

Why?

Because the reviewer may never open ASSUMPTIONS.md.

Everyone opens README.

So instead do

README

Project Overview

Architecture

Assumptions

How to Run

Results

Future Work

Much better.

🚨 First place I want to stop you

Earlier we discussed

aggregate every second.

I'm no longer convinced that's the best approach.

Here's why.

The assignment says

At every one second

But the data is clearly tick-level.

If we aggregate everything into one-second bars,

we lose information.

An HFT company generally dislikes throwing away information unless necessary.

I think there is a better architecture.

Imagine this.

The replay engine processes

Tick 1

↓

Tick 2

↓

Tick 3

↓

Tick 4

exactly as they happened.

No aggregation.

The strategy decides

"I only care once every second."

That is very different.

Now tomorrow,

another strategy may say

I care about every tick.

No changes to the replay engine.

This is much more extensible.

This is how many professional backtesting systems work.

So I would not aggregate the raw data.

Instead,

keep raw ticks.

🚨 Second place I'd stop

Earlier I suggested loading everything into RAM.

I'm not sure anymore.

Let's estimate.

Suppose

60,000 files

Average

3 MB each

That's

180 GB

Impossible.

Instead

I'd load

only today's files.

Even better,

only today's

Nearest expiry

+

NIFTY

+

BANKNIFTY

Already much smaller.

So

no global preload.

Daily preload.

🚨 Third place

Earlier I suggested

unordered_map<string,...>

Still okay,

but I think we can do better.

Instead,

create

Instrument

objects.

Example

Instrument
{
    Underlying

    Expiry

    Strike

    Type
}

Then

MarketData

stores

Instrument*

↓

Ticks

instead of

string

↓

ticks.

Less parsing later.

What architecture would impress me?

I think something like this.

                    Backtester
                         │
          ┌──────────────┴──────────────┐
          │                             │
          ▼                             ▼
    Market Replay                 Portfolio
          │                             ▲
          ▼                             │
      Strategy ─────────► Orders ───────┘
          │
          ▼
     Analytics

Notice

Everything depends only on interfaces.

Not implementations.

Another thing I'd change

I would not name the strategy

ATMStrategy

I'd define

Strategy

Then

ATMStraddleStrategy

Much more descriptive.

Because

the strategy isn't

ATM.

It is

ATM

Long CE

Long PE.

That's called a

Long ATM Straddle.

Knowing that terminology shows you've done a little research.

Let's talk about the replay engine

This is the module I think matters most.

It should not know anything about trading.

Its only responsibility is

Read next market event

↓

Update market state

↓

Notify listeners

That's all.

No buying.

No selling.

No PnL.

Just replay.

That separation is extremely clean.

If I were the interviewer...

The very first thing I'd ask is

Explain your architecture.

Not

Explain your PnL formula.

That's why I think we should spend a little extra effort on the design before implementation.

Here's how I'd like us to proceed

Rather than writing the README immediately, I think there's one more thing we should do first: design the complete system on paper.

By that I mean identifying:

the modules,
the classes,
the responsibilities of each class,
the data flow,
and the interfaces between them.

Once that design is stable, writing the README, implementing the code, and even explaining it in an interview become much easier because everything is consistent.

I also want to be transparent: if at any point I think we're over-engineering for an internship assignment, or conversely taking shortcuts that would hurt the quality of the submission, I'll stop us and explain why. That's exactly how I'd review this if we were working together on the project.