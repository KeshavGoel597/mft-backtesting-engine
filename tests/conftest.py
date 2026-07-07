from __future__ import annotations

import csv
import datetime as dt
from pathlib import Path

import pytest


def _write_csv(path: Path, rows: list[list[object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerows(rows)


def _futures_rows(trading_date: dt.date, base_price: float) -> list[list[object]]:
    start = dt.datetime.combine(trading_date, dt.time(9, 15))
    rows: list[list[object]] = []
    for index in range(120):
        timestamp = start + dt.timedelta(seconds=index)
        rows.append([
            timestamp.strftime("%Y%m%d"),
            timestamp.strftime("%H:%M:%S"),
            f"{base_price + index * 0.5:.2f}",
            1000 + index,
            500 + index,
        ])
    return rows


def _option_rows(trading_date: dt.date, option_base_price: float) -> list[list[object]]:
    start = dt.datetime.combine(trading_date, dt.time(9, 15))
    rows: list[list[object]] = []
    for index in range(5):
        timestamp = start + dt.timedelta(minutes=index)
        rows.append([
            timestamp.strftime("%Y-%m-%d"),
            timestamp.strftime("%H:%M:%S"),
            f"{option_base_price + index * 0.25:.2f}",
            10 + index,
            1 + index,
        ])
    return rows


def _populate_day(day_dir: Path, trading_date: dt.date, rich_data: bool) -> None:
    futures_dir = day_dir / "Futures (Continuous)"
    options_dir = day_dir / "Options"
    futures_dir.mkdir(parents=True, exist_ok=True)
    options_dir.mkdir(parents=True, exist_ok=True)

    if not rich_data:
        return

    expiry = dt.date(2022, 11, 3)
    strike_ranges = {
        "NIFTY": range(17900, 19450, 50),
        "BANKNIFTY": range(40000, 41550, 50),
    }
    atm_prices = {"NIFTY": 18100.0, "BANKNIFTY": 43200.0}

    _write_csv(futures_dir / "NIFTY-I.csv", _futures_rows(trading_date, 18100.0))
    _write_csv(futures_dir / "BANKNIFTY-I.csv", _futures_rows(trading_date, 43200.0))

    for underlying, strikes in strike_ranges.items():
        for strike in strikes:
            for option_type in ("CE", "PE"):
                symbol = f"{underlying}{expiry:%y%m%d}{strike}{option_type}"
                intrinsic_offset = abs(strike - int(atm_prices[underlying])) / 50.0
                option_base_price = 100.0 + intrinsic_offset + (0.0 if option_type == "CE" else 5.0)
                _write_csv(
                    options_dir / f"{symbol}.csv",
                    _option_rows(trading_date, option_base_price),
                )


@pytest.fixture(scope="session")
def sample_data_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("allData")
    start_date = dt.date(2022, 11, 1)

    for offset in range(21):
        trading_date = start_date + dt.timedelta(days=offset)
        day_dir = root / f"NSE_{trading_date:%Y%m%d}"
        _populate_day(day_dir, trading_date, rich_data=(offset == 0))

    return root