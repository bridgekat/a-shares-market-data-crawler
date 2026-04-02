from pathlib import Path

import requests

from .types import Symbol
from .fetch import (
    fetch_symbol_list,
    fetch_daily_prices,
    fetch_equity_structures,
    fetch_dividends,
    fetch_balance_sheets,
    fetch_income_statements,
    fetch_cash_flow_statements,
)
from .parse import (
    parse_symbol_list,
    parse_daily_prices,
    parse_dividends,
    parse_equity_structures,
    parse_balance_sheets,
    parse_income_statements,
    parse_cash_flow_statements,
    parse_indirect_statements,
)


def download_symbol_list(session: requests.Session, data_dir: Path) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    file_path_raw = data_dir / "symbol_list_raw.csv"
    file_path = data_dir / "symbol_list.csv"

    if not file_path.exists():
        raw = fetch_symbol_list(session)
        raw.to_csv(file_path_raw, index=False)

        data = parse_symbol_list(raw)
        data.to_csv(file_path, index=True)


def download_daily_prices(session: requests.Session, symbol: Symbol, data_dir: Path) -> None:
    history_dir = data_dir / "a_shares_history"
    history_dir.mkdir(parents=True, exist_ok=True)
    file_path_raw = history_dir / f"{symbol}.daily_prices_raw.csv"
    file_path = history_dir / f"{symbol}.daily_prices.csv"

    if not file_path.exists():
        raw = fetch_daily_prices(session, symbol)
        if raw is not None:
            raw.to_csv(file_path_raw, index=False)

        data = parse_daily_prices(raw)
        data.to_csv(file_path, index=True)


def download_equity_structures(session: requests.Session, symbol: Symbol, data_dir: Path) -> None:
    history_dir = data_dir / "a_shares_history"
    history_dir.mkdir(parents=True, exist_ok=True)
    file_path_raw = history_dir / f"{symbol}.equity_structures_raw.csv"
    file_path = history_dir / f"{symbol}.equity_structures.csv"

    if not file_path.exists():
        raw = fetch_equity_structures(session, symbol)
        if raw is not None:
            raw.to_csv(file_path_raw, index=False)

        data = parse_equity_structures(raw)
        data.to_csv(file_path, index=True)


def download_dividends(session: requests.Session, symbol: Symbol, data_dir: Path) -> None:
    history_dir = data_dir / "a_shares_history"
    history_dir.mkdir(parents=True, exist_ok=True)
    file_path_raw = history_dir / f"{symbol}.dividends_raw.csv"
    file_path = history_dir / f"{symbol}.dividends.csv"

    if not file_path.exists():
        raw = fetch_dividends(session, symbol)
        if raw is not None:
            raw.to_csv(file_path_raw, index=False)

        data = parse_dividends(raw)
        data.to_csv(file_path, index=True)


def download_balance_sheets(session: requests.Session, symbol: Symbol, data_dir: Path) -> None:
    history_dir = data_dir / "a_shares_history"
    history_dir.mkdir(parents=True, exist_ok=True)
    file_path_raw = history_dir / f"{symbol}.balance_sheets_raw.csv"
    file_path = history_dir / f"{symbol}.balance_sheets.csv"

    if not file_path.exists():
        raw = fetch_balance_sheets(session, symbol)
        if raw is not None:
            raw.to_csv(file_path_raw, index=False)

        data = parse_balance_sheets(raw)
        data.to_csv(file_path, index=True)


def download_income_statements(session: requests.Session, symbol: Symbol, data_dir: Path) -> None:
    history_dir = data_dir / "a_shares_history"
    history_dir.mkdir(parents=True, exist_ok=True)
    file_path_raw = history_dir / f"{symbol}.income_statements_raw.csv"
    file_path = history_dir / f"{symbol}.income_statements.csv"

    if not file_path.exists():
        raw = fetch_income_statements(session, symbol)
        if raw is not None:
            raw.to_csv(file_path_raw, index=False)

        data = parse_income_statements(raw)
        data.to_csv(file_path, index=True)


def download_cash_flow_statements(session: requests.Session, symbol: Symbol, data_dir: Path) -> None:
    history_dir = data_dir / "a_shares_history"
    history_dir.mkdir(parents=True, exist_ok=True)
    file_path_raw = history_dir / f"{symbol}.cash_flow_statements_raw.csv"
    file_path_direct = history_dir / f"{symbol}.cash_flow_statements.csv"
    file_path_indirect = history_dir / f"{symbol}.indirect_statements.csv"

    if not file_path_direct.exists() or not file_path_indirect.exists():
        raw = fetch_cash_flow_statements(session, symbol)
        if raw is not None:
            raw.to_csv(file_path_raw, index=False)

        direct_data = parse_cash_flow_statements(raw)
        direct_data.to_csv(file_path_direct, index=True)
        indirect_data = parse_indirect_statements(raw)
        indirect_data.to_csv(file_path_indirect, index=True)
