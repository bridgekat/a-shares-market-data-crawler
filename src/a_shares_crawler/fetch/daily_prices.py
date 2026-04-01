from typing import Optional

import requests
import pandas as pd

from ..types import Symbol
from ..session import REQUEST_PARAMS
from .utils import exchange_market_code


def fetch_daily_prices(
    session: requests.Session,
    symbol: Symbol,
    start_date: Optional[pd.Timestamp] = None,
    end_date: Optional[pd.Timestamp] = None,
    timeout: int = 15,
) -> Optional[pd.DataFrame]:
    """Fetches the daily price history for a given A-shares stock from EastMoney.

    Returns the list as a [DataFrame][pandas.DataFrame] containing the raw data.

    - Webpage: https://quote.eastmoney.com/concept/sz000001.html
    - API entry point: https://push2his.eastmoney.com/api/qt/stock/kline/get
    """
    assert timeout > 0

    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"

    # Copy parameters to avoid modifying the original
    params = REQUEST_PARAMS.copy()
    params["secid"] = (
        f"{exchange_market_code(symbol.exchange):01}.{symbol.number:06}"  # Security ID
    )
    params["klt"] = "101"  # Candlestick type, 101: daily, 102: weekly, 103: monthly
    params["fqt"] = "0"  # Adjustment type, 0: unadjusted, 1: backward, 2: forward
    params["beg"] = (start_date or pd.Timestamp(0)).strftime("%Y%m%d")  # Start date
    params["end"] = (end_date or pd.Timestamp("now")).strftime("%Y%m%d")  # End date
    params["fields1"] = "f1,f5"  # Info fields to fetch
    params["fields2"] = "f51,f52,f53,f54,f55,f56,f57"  # Candlestick fields to fetch

    # Fetch the data
    r = session.get(url, params=params, timeout=timeout)
    rj = r.json()
    df = pd.DataFrame(
        [item.split(",") for item in rj["data"]["klines"]],
        columns=["date", "open", "close", "high", "low", "volume", "amount"],
    )
    return df
