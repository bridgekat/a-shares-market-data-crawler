
import requests
import pandas as pd

from ..types import Symbol
from .utils import fetch_paginated


def fetch_equity_structures(
    session: requests.Session,
    symbol: Symbol,
    start_date: pd.Timestamp | None = None,
    end_date: pd.Timestamp | None = None,
    timeout: int = 15,
) -> pd.DataFrame | None:
    """Fetches the equity structure history for a given A-shares stock from EastMoney.

    Returns the list as a [DataFrame][pandas.DataFrame] containing the raw data.

    - Webpage: https://emweb.securities.eastmoney.com/pc_hsf10/pages/index.html?code=SZ000001#/gbjg
    - API entry point: https://datacenter.eastmoney.com/securities/api/data/get
    """
    assert timeout > 0

    url = "https://datacenter.eastmoney.com/securities/api/data/get"

    # No need to use the global REQUEST_PARAMS here (different domains)
    params = {}
    params["type"] = "RPT_F10_EH_EQUITY"
    params["sty"] = "ALL"
    params["filter"] = (
        f'(SECUCODE="{symbol}")'
        + (f"(NOTICE_DATE>='{start_date.strftime('%Y-%m-%d')}')" if start_date else "")
        + (f"(NOTICE_DATE<='{end_date.strftime('%Y-%m-%d')}')" if end_date else "")
    )
    params["st"] = "NOTICE_DATE"  # Sort by field
    params["sr"] = 1  # Page ordering, 1 for ascending, -1 for descending
    params["source"] = "HSF10"
    params["client"] = "PC"
    params["v"] = "03483956563750341"

    # Fetch the data
    df = fetch_paginated(session, url, params, page_size=500, timeout=timeout)
    return df
