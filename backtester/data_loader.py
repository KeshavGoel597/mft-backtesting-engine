"""
Data Loader — reads CSV files and builds instrument metadata.

Responsibilities:
  1. Parse option filenames into Instrument objects.
  2. Load CSV tick data (futures and options).
  3. Build an InstrumentRegistry — the "security master" for a trading day.
  4. Basic data validation (negative prices, empty files, malformed names).

Design:
  - All file I/O is confined to this module.
  - Returns domain objects (Tick, FuturesTick, Instrument).
  - No trading logic.
"""

from __future__ import annotations

import csv
import datetime as dt
import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from .models import FuturesTick, Instrument, OptionType, Tick

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Option filename regex:
#   Group 1: underlying  (NIFTY | BANKNIFTY | FINNIFTY …)
#   Group 2: expiry      (6 digits, YYMMDD)
#   Group 3: strike      (digits, variable length)
#   Group 4: option type (CE | PE)
_OPTION_FILENAME_RE = re.compile(
    r"^([A-Z]+?)(\d{6})(\d+)(CE|PE)$"
)

SUPPORTED_UNDERLYINGS = {"NIFTY", "BANKNIFTY"}


# ---------------------------------------------------------------------------
# Filename Parser
# ---------------------------------------------------------------------------

def parse_option_filename(filename_stem: str) -> Optional[Instrument]:
    """
    Parse an option filename (without .csv) into an Instrument.

    Examples:
        NIFTY22110318100CE  → Instrument(NIFTY, 2022-11-03, 18100, CE)
        BANKNIFTY22112443200CE → Instrument(BANKNIFTY, 2022-11-24, 43200, CE)

    Returns None if the filename does not match the expected format.
    """
    m = _OPTION_FILENAME_RE.match(filename_stem)
    if m is None:
        return None

    underlying = m.group(1)
    expiry_str = m.group(2)      # YYMMDD
    strike_str = m.group(3)
    opt_type_str = m.group(4)

    try:
        expiry = dt.datetime.strptime(expiry_str, "%y%m%d").date()
        strike = int(strike_str)
        option_type = OptionType(opt_type_str)
    except (ValueError, KeyError):
        logger.warning("Could not parse option filename: %s", filename_stem)
        return None

    return Instrument(
        underlying=underlying,
        expiry=expiry,
        strike=strike,
        option_type=option_type,
        symbol=filename_stem,
    )


# ---------------------------------------------------------------------------
# CSV Reader helpers
# ---------------------------------------------------------------------------

def _parse_csv_row(row: list, date_hint: dt.date) -> Tuple[dt.datetime, float, int, int]:
    """
    Parse one CSV row: Date,Time,Price,Volume,OpenInterest
    Returns (timestamp, price, volume, oi).
    """
    date_str = row[0].strip()
    time_str = row[1].strip()
    price = float(row[2].strip())
    volume = int(row[3].strip())
    oi = int(row[4].strip())

    # Parse timestamp — date may be YYYYMMDD or YYYY-MM-DD
    if "-" in date_str:
        date_part = dt.datetime.strptime(date_str, "%Y-%m-%d").date()
    else:
        date_part = dt.datetime.strptime(date_str, "%Y%m%d").date()

    time_part = dt.datetime.strptime(time_str, "%H:%M:%S").time()
    timestamp = dt.datetime.combine(date_part, time_part)

    return timestamp, price, volume, oi


def load_futures_ticks(
    csv_path: Path,
    underlying: str,
    date_hint: dt.date,
) -> List[FuturesTick]:
    """Load all ticks from a futures CSV file."""
    ticks: List[FuturesTick] = []
    if not csv_path.exists():
        logger.warning("Futures file not found: %s", csv_path)
        return ticks

    with open(csv_path, "r", newline="") as f:
        reader = csv.reader(f)
        for row_num, row in enumerate(reader, 1):
            if len(row) < 5:
                logger.debug("Skipping short row %d in %s", row_num, csv_path.name)
                continue
            try:
                ts, price, volume, oi = _parse_csv_row(row, date_hint)
            except (ValueError, IndexError) as exc:
                logger.debug("Bad row %d in %s: %s", row_num, csv_path.name, exc)
                continue

            if price <= 0:
                logger.debug("Non-positive price at row %d in %s", row_num, csv_path.name)
                continue

            ticks.append(FuturesTick(
                underlying=underlying,
                timestamp=ts,
                price=price,
                volume=volume,
                open_interest=oi,
            ))

    logger.info("Loaded %d futures ticks from %s", len(ticks), csv_path.name)
    return ticks


def load_option_ticks(
    csv_path: Path,
    instrument: Instrument,
    date_hint: dt.date,
) -> List[Tick]:
    """Load all ticks from an option CSV file."""
    ticks: List[Tick] = []
    if not csv_path.exists():
        logger.warning("Option file not found: %s", csv_path)
        return ticks

    with open(csv_path, "r", newline="") as f:
        reader = csv.reader(f)
        for row_num, row in enumerate(reader, 1):
            if len(row) < 5:
                continue
            try:
                ts, price, volume, oi = _parse_csv_row(row, date_hint)
            except (ValueError, IndexError):
                continue

            if price <= 0:
                continue

            ticks.append(Tick(
                instrument=instrument,
                timestamp=ts,
                price=price,
                volume=volume,
                open_interest=oi,
            ))

    logger.info("Loaded %d option ticks from %s", len(ticks), csv_path.name)
    return ticks


# ---------------------------------------------------------------------------
# Instrument Registry — the "Security Master" for one trading day
# ---------------------------------------------------------------------------

@dataclass
class InstrumentRegistry:
    """
    All instruments available on a given trading day.

    Built once per day by scanning the Options folder.
    Provides fast lookups by underlying, expiry, strike, and type.
    """
    date: dt.date
    instruments: List[Instrument] = field(default_factory=list)

    # Indexes built after population
    _by_underlying: Dict[str, List[Instrument]] = field(
        default_factory=dict, repr=False
    )
    _expiries_by_underlying: Dict[str, List[dt.date]] = field(
        default_factory=dict, repr=False
    )

    def build_indexes(self) -> None:
        """Build fast-lookup indexes. Call after instruments list is populated."""
        self._by_underlying.clear()
        self._expiries_by_underlying.clear()

        for inst in self.instruments:
            self._by_underlying.setdefault(inst.underlying, []).append(inst)

        for und, insts in self._by_underlying.items():
            expiries = sorted({i.expiry for i in insts})
            self._expiries_by_underlying[und] = expiries

    def get_instruments(
        self,
        underlying: str,
        expiry: Optional[dt.date] = None,
        strike: Optional[int] = None,
        option_type: Optional[OptionType] = None,
    ) -> List[Instrument]:
        """Filter instruments by any combination of criteria."""
        result = self._by_underlying.get(underlying, [])
        if expiry is not None:
            result = [i for i in result if i.expiry == expiry]
        if strike is not None:
            result = [i for i in result if i.strike == strike]
        if option_type is not None:
            result = [i for i in result if i.option_type == option_type]
        return result

    def nearest_expiry(self, underlying: str, as_of: dt.date) -> Optional[dt.date]:
        """
        Return the nearest expiry >= as_of for the given underlying.
        If the trading date IS an expiry date, that expiry is used.
        """
        expiries = self._expiries_by_underlying.get(underlying, [])
        for exp in expiries:
            if exp >= as_of:
                return exp
        return None

    def available_strikes(
        self, underlying: str, expiry: dt.date
    ) -> List[int]:
        """Return sorted list of strikes available for (underlying, expiry)."""
        insts = self.get_instruments(underlying, expiry=expiry)
        return sorted({i.strike for i in insts})


# ---------------------------------------------------------------------------
# Day Loader — top-level function to load all data for one trading day
# ---------------------------------------------------------------------------

@dataclass
class DayData:
    """All market data for a single trading day."""
    date: dt.date
    registry: InstrumentRegistry
    futures_ticks: Dict[str, List[FuturesTick]]     # underlying → ticks
    option_ticks: Dict[Instrument, List[Tick]]       # instrument → ticks


def load_day(day_dir: Path) -> DayData:
    """
    Load all relevant data for one trading day.

    Args:
        day_dir: Path to e.g. allData/NSE_20221101/

    Returns:
        DayData with registry, futures ticks, and option ticks
        for NIFTY and BANKNIFTY only.
    """
    # Parse date from folder name: NSE_YYYYMMDD
    folder_name = day_dir.name
    date_str = folder_name.replace("NSE_", "")
    trading_date = dt.datetime.strptime(date_str, "%Y%m%d").date()

    futures_dir = day_dir / "Futures (Continuous)"
    options_dir = day_dir / "Options"

    # --- Load futures ---
    futures_ticks: Dict[str, List[FuturesTick]] = {}
    for underlying in SUPPORTED_UNDERLYINGS:
        fut_path = futures_dir / f"{underlying}-I.csv"
        futures_ticks[underlying] = load_futures_ticks(fut_path, underlying, trading_date)

    # --- Build instrument registry from Options folder ---
    registry = InstrumentRegistry(date=trading_date)
    instrument_file_map: Dict[Instrument, Path] = {}

    if options_dir.exists():
        for fname in sorted(os.listdir(options_dir)):
            if not fname.endswith(".csv"):
                continue
            stem = fname[:-4]  # remove .csv
            inst = parse_option_filename(stem)
            if inst is None:
                continue
            if inst.underlying not in SUPPORTED_UNDERLYINGS:
                continue
            registry.instruments.append(inst)
            instrument_file_map[inst] = options_dir / fname

    registry.build_indexes()
    logger.info(
        "Day %s: %d instruments registered (%s)",
        trading_date,
        len(registry.instruments),
        ", ".join(
            f"{u}: {len(registry.get_instruments(u))}"
            for u in SUPPORTED_UNDERLYINGS
        ),
    )

    # --- Load option ticks only for nearest-expiry instruments ---
    # Pre-filter: only load ticks for instruments we might trade
    # This is a significant performance optimization — avoids loading
    # hundreds of far-expiry option files we'll never use.
    option_ticks: Dict[Instrument, List[Tick]] = {}
    for underlying in SUPPORTED_UNDERLYINGS:
        nearest_exp = registry.nearest_expiry(underlying, trading_date)
        if nearest_exp is None:
            logger.warning("No expiry found for %s on %s", underlying, trading_date)
            continue

        relevant_instruments = registry.get_instruments(underlying, expiry=nearest_exp)
        for inst in relevant_instruments:
            csv_path = instrument_file_map.get(inst)
            if csv_path is None:
                continue
            ticks = load_option_ticks(csv_path, inst, trading_date)
            if ticks:
                option_ticks[inst] = ticks

    logger.info(
        "Day %s: loaded option ticks for %d instruments",
        trading_date,
        len(option_ticks),
    )

    return DayData(
        date=trading_date,
        registry=registry,
        futures_ticks=futures_ticks,
        option_ticks=option_ticks,
    )


def discover_trading_days(data_root: Path) -> List[Path]:
    """
    Return sorted list of day directories under allData/.
    """
    if not data_root.exists():
        raise FileNotFoundError(f"Data root not found: {data_root}")

    day_dirs = sorted(
        p for p in data_root.iterdir()
        if p.is_dir() and p.name.startswith("NSE_")
    )
    logger.info("Discovered %d trading days", len(day_dirs))
    return day_dirs
