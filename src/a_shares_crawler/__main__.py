import argparse
from pathlib import Path

from tqdm import tqdm
import pandas as pd

from .types import Symbol
from .session import load_config, create_session
from .download import (
    DATA_DIR,
    download_symbol_list,
    download_daily_prices,
    download_equity_structures,
    download_dividends,
    download_balance_sheets,
    download_income_statements,
)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config.json"),
        help="path to the JSON configuration file (default: config.json)",
    )
    args = parser.parse_args()

    load_config(args.config)
    session = create_session()

    print("Downloading stock symbol list...")
    download_symbol_list(session)

    symbols_df = pd.read_csv(DATA_DIR / "symbol_list.csv")
    symbols = [Symbol.from_str(s) for s in symbols_df["symbol"]]

    print("Downloading daily prices...")
    for symbol in tqdm(symbols):
        download_daily_prices(session, symbol)

    print("Downloading financial reports...")
    for symbol in tqdm(symbols):
        download_equity_structures(session, symbol)
        download_dividends(session, symbol)
        download_balance_sheets(session, symbol)
        download_income_statements(session, symbol)
