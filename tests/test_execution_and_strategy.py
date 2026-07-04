import datetime as dt
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backtester.data_loader import InstrumentRegistry
from backtester.execution import ExecutionConfig, ExecutionEngine
from backtester.market_state import MarketState
from backtester.models import FuturesTick, Instrument, OptionType, Order, Side, Tick
from backtester.strategy import ATMStraddleStrategy


def make_option(symbol: str, strike: int, option_type: OptionType) -> Instrument:
    return Instrument(
        underlying="NIFTY",
        expiry=dt.date(2022, 11, 3),
        strike=strike,
        option_type=option_type,
        symbol=symbol,
    )


def test_execution_engine_rejects_stale_atomic_batch():
    ce = make_option("NIFTY22110318000CE", 18000, OptionType.CE)
    pe = make_option("NIFTY22110318000PE", 18000, OptionType.PE)
    market_state = MarketState()
    quote_time = dt.datetime(2022, 11, 1, 9, 15, 0)

    market_state.update_option_tick(Tick(ce, quote_time, 100.0, 10, 1))
    market_state.update_option_tick(Tick(pe, quote_time, 110.0, 12, 1))

    engine = ExecutionEngine(
        ExecutionConfig(max_quote_age=dt.timedelta(seconds=5))
    )
    trades = engine.execute(
        [
            Order(ce, Side.BUY, timestamp=quote_time, reason="ENTER"),
            Order(pe, Side.BUY, timestamp=quote_time, reason="ENTER"),
        ],
        market_state,
        quote_time + dt.timedelta(seconds=10),
        atomic_batch=True,
    )

    assert trades == []


def test_execution_engine_applies_slippage_and_fees():
    ce = make_option("NIFTY22110318000CE", 18000, OptionType.CE)
    market_state = MarketState()
    quote_time = dt.datetime(2022, 11, 1, 9, 15, 0)
    market_state.update_option_tick(Tick(ce, quote_time, 100.0, 10, 1))

    engine = ExecutionEngine(
        ExecutionConfig(slippage_bps=10.0, fee_per_order=2.5)
    )
    trades = engine.execute(
        [Order(ce, Side.BUY, timestamp=quote_time, reason="ENTER")],
        market_state,
        quote_time,
        atomic_batch=True,
    )

    assert len(trades) == 1
    assert trades[0].reference_price == 100.0
    assert trades[0].price == pytest.approx(100.1)
    assert trades[0].fees == 2.5


def test_strategy_state_changes_only_after_fill_confirmation():
    ce = make_option("NIFTY22110318000CE", 18000, OptionType.CE)
    pe = make_option("NIFTY22110318000PE", 18000, OptionType.PE)
    registry = InstrumentRegistry(date=dt.date(2022, 11, 1), instruments=[ce, pe])
    registry.build_indexes()

    market_state = MarketState()
    ts = dt.datetime(2022, 11, 1, 9, 15, 0)
    market_state.update_futures_tick(FuturesTick("NIFTY", ts, 18010.0, 1, 1))
    market_state.update_option_tick(Tick(ce, ts, 100.0, 10, 1))
    market_state.update_option_tick(Tick(pe, ts, 110.0, 12, 1))

    strategy = ATMStraddleStrategy("NIFTY")
    orders = strategy.on_market_update(market_state, ts, registry, registry.date)
    assert len(orders) == 2

    # No fill confirmation yet, so the strategy should not think it holds inventory.
    assert strategy.on_day_end(market_state, ts, registry, registry.date) == []

    engine = ExecutionEngine()
    trades = engine.execute(orders, market_state, ts, atomic_batch=True)
    strategy.on_trades(trades, ts)

    eod_orders = strategy.on_day_end(market_state, ts, registry, registry.date)
    assert len(eod_orders) == 2
    assert all(order.side == Side.SELL for order in eod_orders)
