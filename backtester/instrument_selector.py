"""
Instrument Selector — finds tradeable instruments based on criteria.

Separated from Strategy so that different selection logic
(nearest expiry, second expiry, ATM ± N) can be swapped independently.
"""

from __future__ import annotations

from bisect import bisect_left
import datetime as dt
from abc import ABC, abstractmethod
from typing import Optional, Tuple

from .data_loader import InstrumentRegistry
from .market_state import MarketState
from .models import Instrument, OptionType


class InstrumentSelector(ABC):
    """Base class for instrument selection logic."""

    @abstractmethod
    def select_strike(
        self,
        underlying: str,
        market_state: MarketState,
        registry: InstrumentRegistry,
        trading_date: dt.date,
    ) -> Optional[int]:
        """
        Return the strike price to trade, or None if no valid strike.
        """
        ...

    @abstractmethod
    def get_instruments(
        self,
        underlying: str,
        strike: int,
        registry: InstrumentRegistry,
        trading_date: dt.date,
    ) -> Tuple[Optional[Instrument], Optional[Instrument]]:
        """
        Return (CE instrument, PE instrument) for the given strike.
        """
        ...


class ATMSelector(InstrumentSelector):
    """
    Selects the At-The-Money strike: the strike closest to the
    current futures price, from the nearest expiry.

    Tie-breaking: if futures price is exactly between two strikes,
    select the lower strike (convention).
    """

    def __init__(self) -> None:
        self._expiry_cache: dict[tuple[str, dt.date], Optional[dt.date]] = {}

    def _get_nearest_expiry(
        self,
        underlying: str,
        registry: InstrumentRegistry,
        trading_date: dt.date,
    ) -> Optional[dt.date]:
        key = (underlying, trading_date)
        if key not in self._expiry_cache:
            self._expiry_cache[key] = registry.nearest_expiry(underlying, trading_date)
        return self._expiry_cache[key]

    def select_strike(
        self,
        underlying: str,
        market_state: MarketState,
        registry: InstrumentRegistry,
        trading_date: dt.date,
    ) -> Optional[int]:
        futures_price = market_state.get_futures_price(underlying)
        if futures_price is None:
            return None

        expiry = self._get_nearest_expiry(underlying, registry, trading_date)
        if expiry is None:
            return None

        strikes = registry.available_strikes(underlying, expiry)
        if not strikes:
            return None

        insert_at = bisect_left(strikes, futures_price)
        if insert_at == 0:
            return strikes[0]
        if insert_at >= len(strikes):
            return strikes[-1]

        lower = strikes[insert_at - 1]
        upper = strikes[insert_at]
        if abs(lower - futures_price) <= abs(upper - futures_price):
            return lower
        return upper

    def get_instruments(
        self,
        underlying: str,
        strike: int,
        registry: InstrumentRegistry,
        trading_date: dt.date,
    ) -> Tuple[Optional[Instrument], Optional[Instrument]]:
        expiry = self._get_nearest_expiry(underlying, registry, trading_date)
        if expiry is None:
            return None, None

        ce = registry.get_instrument(underlying, expiry, strike, OptionType.CE)
        pe = registry.get_instrument(underlying, expiry, strike, OptionType.PE)
        return ce, pe
