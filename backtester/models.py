"""
Domain model for the backtesting framework.

Core value objects and entities that represent the trading domain.
These are pure data containers with no I/O dependencies.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class OptionType(Enum):
    """CE = Call, PE = Put."""
    CE = "CE"
    PE = "PE"


class Side(Enum):
    """Order / trade direction."""
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    """For extensibility — currently only MARKET is used."""
    MARKET = "MARKET"


# ---------------------------------------------------------------------------
# Instrument
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Instrument:
    """
    Uniquely identifies an option contract.

    Parsed once from the filename (e.g. NIFTY22110318100CE)
    and reused throughout the framework.  Frozen so it can be
    used as a dict key / set member.
    """
    underlying: str            # e.g. "NIFTY", "BANKNIFTY"
    expiry: dt.date            # e.g. 2022-11-03
    strike: int                # e.g. 18100
    option_type: OptionType    # CE or PE
    symbol: str = ""           # original filename stem, e.g. "NIFTY22110318100CE"

    def __repr__(self) -> str:
        return self.symbol or f"{self.underlying}{self.expiry:%y%m%d}{self.strike}{self.option_type.value}"


# ---------------------------------------------------------------------------
# Tick
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Tick:
    """
    One market data update — represents a single trade/quote from the CSV.
    """
    instrument: Instrument
    timestamp: dt.datetime
    price: float
    volume: int
    open_interest: int


@dataclass(frozen=True)
class FuturesTick:
    """
    One futures market update.  Kept separate from option Tick because
    futures are not traded — they are only used for ATM determination.
    """
    underlying: str            # "NIFTY" or "BANKNIFTY"
    timestamp: dt.datetime
    price: float
    volume: int
    open_interest: int


# ---------------------------------------------------------------------------
# Order & Trade
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Order:
    """
    Intent to trade — produced by Strategy, consumed by Execution Engine.
    """
    instrument: Instrument
    side: Side
    quantity: int = 1
    order_type: OrderType = OrderType.MARKET
    timestamp: Optional[dt.datetime] = None
    reason: str = ""           # human-readable, e.g. "ATM_SHIFT", "EOD_CLOSE"


@dataclass(frozen=True)
class Trade:
    """
    Executed trade — produced by Execution Engine, consumed by Portfolio.
    """
    instrument: Instrument
    side: Side
    quantity: int
    price: float
    timestamp: dt.datetime
    order: Order               # reference back to originating order
    trade_id: int = 0


# ---------------------------------------------------------------------------
# Position
# ---------------------------------------------------------------------------

@dataclass
class Position:
    """
    Tracks a single open position in one instrument.

    Mutable because it gets updated on each mark-to-market.
    """
    instrument: Instrument
    side: Side
    quantity: int
    entry_price: float
    entry_time: dt.datetime
    current_price: float = 0.0
    last_update: Optional[dt.datetime] = None

    @property
    def unrealized_pnl(self) -> float:
        """Mark-to-market PnL for this position."""
        direction = 1 if self.side == Side.BUY else -1
        return direction * (self.current_price - self.entry_price) * self.quantity

    @property
    def is_long(self) -> bool:
        return self.side == Side.BUY

    def mark_to_market(self, price: float, timestamp: dt.datetime) -> None:
        """Update current market price for MTM calculation."""
        self.current_price = price
        self.last_update = timestamp


# ---------------------------------------------------------------------------
# PnL Snapshot (for equity curve)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PnLSnapshot:
    """Point-in-time snapshot of portfolio value."""
    timestamp: dt.datetime
    unrealized_pnl: float
    realized_pnl: float
    total_pnl: float
    num_positions: int
