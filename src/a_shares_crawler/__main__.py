from pathlib import Path
from tqdm import tqdm
import requests
import argparse
import pandas as pd

from .a_shares import *
from . import a_shares_em as em


DATA_DIR = Path(".") / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

HISTORY_DIR = DATA_DIR / "a_shares_history"
HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def download_symbol_list(session: requests.Session) -> None:
    file_path_raw = DATA_DIR / "symbol_list_raw.csv"
    file_path = DATA_DIR / "symbol_list.csv"

    if not file_path.exists():
        raw = em.fetch_symbol_list(session)
        raw.to_csv(file_path_raw, index=False)

        data = em.parse_symbol_list(raw)
        data.to_csv(file_path, index=True)


def download_daily_prices(session: requests.Session, symbol: Symbol) -> None:
    file_path_raw = HISTORY_DIR / f"{symbol}.daily_prices_raw.csv"
    file_path = HISTORY_DIR / f"{symbol}.daily_prices.csv"

    if not file_path.exists():
        raw = em.fetch_daily_prices(session, symbol)
        if raw is not None:
            raw.to_csv(file_path_raw, index=False)

        data = em.parse_daily_prices(raw)
        data.to_csv(file_path, index=True)


def download_equity_structures(session: requests.Session, symbol: Symbol) -> None:
    file_path_raw = HISTORY_DIR / f"{symbol}.equity_structures_raw.csv"
    file_path = HISTORY_DIR / f"{symbol}.equity_structures.csv"

    if not file_path.exists():
        raw = em.fetch_equity_structures(session, symbol)
        if raw is not None:
            raw.to_csv(file_path_raw, index=False)

        data = em.parse_equity_structures(raw)
        data.to_csv(file_path, index=True)


def download_dividends(session: requests.Session, symbol: Symbol) -> None:
    file_path_raw = HISTORY_DIR / f"{symbol}.dividends_raw.csv"
    file_path = HISTORY_DIR / f"{symbol}.dividends.csv"

    if not file_path_raw.exists():
        raw = em.fetch_dividends(session, symbol)
        if raw is not None:
            raw.to_csv(file_path_raw, index=False)

        data = em.parse_dividends(raw)
        data.to_csv(file_path, index=True)


def download_balance_sheets(session: requests.Session, symbol: Symbol) -> None:
    file_path_raw = HISTORY_DIR / f"{symbol}.balance_sheets_raw.csv"
    file_path = HISTORY_DIR / f"{symbol}.balance_sheets.csv"

    if not file_path_raw.exists():
        raw = em.fetch_balance_sheets(session, symbol)
        if raw is not None:
            raw.to_csv(file_path_raw, index=False)

        data = em.parse_balance_sheets(raw)
        data.to_csv(file_path, index=True)


def download_income_statements(session: requests.Session, symbol: Symbol) -> None:
    file_path_raw = HISTORY_DIR / f"{symbol}.income_statements_raw.csv"
    file_path = HISTORY_DIR / f"{symbol}.income_statements.csv"

    if not file_path_raw.exists():
        raw = em.fetch_income_statements(session, symbol)
        if raw is not None:
            raw.to_csv(file_path_raw, index=False)

        data = em.parse_income_statements(raw)
        data.to_csv(file_path, index=True)


# def download_cash_flow_statements(session: requests.Session, symbol: Symbol) -> None:
#     file_path_raw = HISTORY_DIR / f"{symbol}.cash_flow_statements_raw.csv"
#     file_path = HISTORY_DIR / f"{symbol}.cash_flow_statements.csv"

#     if not file_path_raw.exists():
#         raw = em.fetch_cash_flow_statements(session, symbol)
#         if raw is not None:
#             raw.to_csv(file_path_raw, index=False)

#         data = em.parse_cash_flow_statements(raw)
#         data.to_csv(file_path, index=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    args = parser.parse_args()

    session = em.create_session()

    print("Downloading stock symbol list...")
    download_symbol_list(session)

    list = pd.read_csv(DATA_DIR / "symbol_list.csv")
    symbols = [Symbol.from_str(s) for s in list["symbol"]]

    print("Downloading daily prices...")
    for symbol in tqdm(symbols):
        download_daily_prices(session, symbol)

    print("Downloading financial reports...")
    for symbol in tqdm(symbols):
        download_equity_structures(session, symbol)
        download_dividends(session, symbol)
        download_balance_sheets(session, symbol)
        download_income_statements(session, symbol)
        # download_cash_flow_statements(session, symbol)
