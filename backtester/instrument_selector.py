"""
Instrument Selector — finds tradeable instruments based on criteria.

Separated from Strategy so that different selection logic
(nearest expiry, second expiry, ATM ± N) can be swapped independently.
"""

from __future__ import annotations

import datetime as dt
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

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

        # Find closest strike — tie-break to lower
        best_strike = min(strikes, key=lambda s: (abs(s - futures_price), s))
        return best_strike

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

        ce_list = registry.get_instruments(
            underlying, expiry=expiry, strike=strike, option_type=OptionType.CE
        )
        pe_list = registry.get_instruments(
            underlying, expiry=expiry, strike=strike, option_type=OptionType.PE
        )

        ce = ce_list[0] if ce_list else None
        pe = pe_list[0] if pe_list else None
        return ce, pe
