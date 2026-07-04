"""
Tests for Phase 1: Domain Model & Data Loader.

Run:  python -m pytest tests/test_data_loader.py -v
"""

import datetime as dt
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backtester.models import Instrument, OptionType
from backtester.data_loader import (
    parse_option_filename,
    load_day,
    discover_trading_days,
)

DATA_ROOT = Path(__file__).resolve().parent.parent / "allData"


# ---------------------------------------------------------------------------
# Filename parser tests
# ---------------------------------------------------------------------------

class TestFilenameParser:

    def test_nifty_basic(self):
        inst = parse_option_filename("NIFTY22110318100CE")
        assert inst is not None
        assert inst.underlying == "NIFTY"
        assert inst.expiry == dt.date(2022, 11, 3)
        assert inst.strike == 18100
        assert inst.option_type == OptionType.CE

    def test_banknifty(self):
        inst = parse_option_filename("BANKNIFTY22112443200CE")
        assert inst is not None
        assert inst.underlying == "BANKNIFTY"
        assert inst.expiry == dt.date(2022, 11, 24)
        assert inst.strike == 43200
        assert inst.option_type == OptionType.CE

    def test_put(self):
        inst = parse_option_filename("NIFTY22110314550PE")
        assert inst is not None
        assert inst.option_type == OptionType.PE
        assert inst.strike == 14550

    def test_finnifty(self):
        inst = parse_option_filename("FINNIFTY22110719500CE")
        assert inst is not None
        assert inst.underlying == "FINNIFTY"

    def test_invalid_returns_none(self):
        assert parse_option_filename("NIFTY-I") is None
        assert parse_option_filename("") is None
        assert parse_option_filename("RANDOM_FILE") is None


# ---------------------------------------------------------------------------
# Data loading tests (require actual data)
# ---------------------------------------------------------------------------

class TestDayLoader:

    def test_discover_days(self):
        days = discover_trading_days(DATA_ROOT)
        assert len(days) == 21, f"Expected 21 trading days, got {len(days)}"

    def test_load_first_day(self):
        day_dir = DATA_ROOT / "NSE_20221101"
        day_data = load_day(day_dir)

        # Date
        assert day_data.date == dt.date(2022, 11, 1)

        # Futures loaded
        assert "NIFTY" in day_data.futures_ticks
        assert "BANKNIFTY" in day_data.futures_ticks
        assert len(day_data.futures_ticks["NIFTY"]) > 100

        # First futures tick
        first_fut = day_data.futures_ticks["NIFTY"][0]
        assert first_fut.underlying == "NIFTY"
        assert first_fut.price > 17000

        # Registry has instruments
        assert len(day_data.registry.instruments) > 50

        # Nearest expiry for NIFTY on 2022-11-01 should be 2022-11-03
        nearest = day_data.registry.nearest_expiry("NIFTY", dt.date(2022, 11, 1))
        assert nearest == dt.date(2022, 11, 3)

        # Nearest expiry for BANKNIFTY
        nearest_bn = day_data.registry.nearest_expiry("BANKNIFTY", dt.date(2022, 11, 1))
        assert nearest_bn == dt.date(2022, 11, 3)

        # Option ticks loaded for nearest expiry
        nifty_opts = [
            inst for inst in day_data.option_ticks
            if inst.underlying == "NIFTY" and inst.expiry == dt.date(2022, 11, 3)
        ]
        assert len(nifty_opts) > 10, f"Expected multiple NIFTY options, got {len(nifty_opts)}"

    def test_strikes_around_atm(self):
        """Verify we have strikes near the futures price (~18150 for NIFTY)."""
        day_dir = DATA_ROOT / "NSE_20221101"
        day_data = load_day(day_dir)

        nearest = day_data.registry.nearest_expiry("NIFTY", dt.date(2022, 11, 1))
        strikes = day_data.registry.available_strikes("NIFTY", nearest)

        # 18150 should be in or very near the strikes list
        assert 18100 in strikes or 18150 in strikes or 18200 in strikes
        # Strikes should be in 50-pt increments near ATM
        atm_strikes = [s for s in strikes if 17900 <= s <= 18400]
        diffs = [atm_strikes[i+1] - atm_strikes[i] for i in range(len(atm_strikes)-1)]
        assert all(d == 50 for d in diffs), f"Non-50pt spacing found: {diffs}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
