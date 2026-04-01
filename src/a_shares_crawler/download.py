from pathlib import Path

import requests
import pandas as pd

from .types import Symbol
from .fetch import (
    fetch_symbol_list,
    fetch_daily_prices,
    fetch_equity_structures,
    fetch_dividends,
    fetch_balance_sheets,
    fetch_income_statements,
)
from .parse import (
    parse_symbol_list,
    parse_daily_prices,
    parse_dividends,
    parse_equity_structures,
    parse_balance_sheets,
    parse_income_statements,
)


DATA_DIR = Path(".") / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

HISTORY_DIR = DATA_DIR / "a_shares_history"
HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def download_symbol_list(session: requests.Session) -> None:
    file_path_raw = DATA_DIR / "symbol_list_raw.csv"
    file_path = DATA_DIR / "symbol_list.csv"

    if not file_path.exists():
        raw = fetch_symbol_list(session)
        raw.to_csv(file_path_raw, index=False)

        data = parse_symbol_list(raw)
        data.to_csv(file_path, index=True)


def download_daily_prices(session: requests.Session, symbol: Symbol) -> None:
    file_path_raw = HISTORY_DIR / f"{symbol}.daily_prices_raw.csv"
    file_path = HISTORY_DIR / f"{symbol}.daily_prices.csv"

    if not file_path.exists():
        raw = fetch_daily_prices(session, symbol)
        if raw is not None:
            raw.to_csv(file_path_raw, index=False)

        data = parse_daily_prices(raw)
        data.to_csv(file_path, index=True)


def download_equity_structures(session: requests.Session, symbol: Symbol) -> None:
    file_path_raw = HISTORY_DIR / f"{symbol}.equity_structures_raw.csv"
    file_path = HISTORY_DIR / f"{symbol}.equity_structures.csv"

    if not file_path.exists():
        raw = fetch_equity_structures(session, symbol)
        if raw is not None:
            raw.to_csv(file_path_raw, index=False)

        data = parse_equity_structures(raw)
        data.to_csv(file_path, index=True)


def download_dividends(session: requests.Session, symbol: Symbol) -> None:
    file_path_raw = HISTORY_DIR / f"{symbol}.dividends_raw.csv"
    file_path = HISTORY_DIR / f"{symbol}.dividends.csv"

    if not file_path_raw.exists():
        raw = fetch_dividends(session, symbol)
        if raw is not None:
            raw.to_csv(file_path_raw, index=False)

        data = parse_dividends(raw)
        data.to_csv(file_path, index=True)


def download_balance_sheets(session: requests.Session, symbol: Symbol) -> None:
    file_path_raw = HISTORY_DIR / f"{symbol}.balance_sheets_raw.csv"
    file_path = HISTORY_DIR / f"{symbol}.balance_sheets.csv"

    if not file_path_raw.exists():
        raw = fetch_balance_sheets(session, symbol)
        if raw is not None:
            raw.to_csv(file_path_raw, index=False)

        data = parse_balance_sheets(raw)
        data.to_csv(file_path, index=True)


def download_income_statements(session: requests.Session, symbol: Symbol) -> None:
    file_path_raw = HISTORY_DIR / f"{symbol}.income_statements_raw.csv"
    file_path = HISTORY_DIR / f"{symbol}.income_statements.csv"

    if not file_path_raw.exists():
        raw = fetch_income_statements(session, symbol)
        if raw is not None:
            raw.to_csv(file_path_raw, index=False)

        data = parse_income_statements(raw)
        data.to_csv(file_path, index=True)
