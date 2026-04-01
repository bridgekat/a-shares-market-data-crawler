from typing import Optional

import requests
import pandas as pd

from ..types import Symbol
from .utils import fetch_paginated


def fetch_original_reports_raw(
    session: requests.Session,
    symbol: Symbol,
    timeout: int = 15,
) -> Optional[pd.DataFrame]:
    """Fetches the original financial reports for a given A-shares stock from EastMoney.

    Returns the list as a [DataFrame][pandas.DataFrame] containing the raw data.

    - Webpage: https://emweb.securities.eastmoney.com/pc_hsf10/pages/index.html?code=SZ000001#/cwfx/cwbb
    - API entry point: https://datacenter.eastmoney.com/securities/api/data/get
    """
    assert timeout > 0

    url = "https://datacenter.eastmoney.com/securities/api/data/get"

    # No need to use the global REQUEST_PARAMS here (different domains)
    params = {}
    params["type"] = "RPT_PCF10_ORIG_REPORT"
    params["sty"] = "ALL"
    params["filter"] = f'(SECUCODE="{symbol}")'
    params["st"] = "REPORT_DATE"  # Sort by field
    params["sr"] = 1  # Page ordering, 1 for ascending, -1 for descending
    params["source"] = "HSF10"
    params["client"] = "PC"
    params["v"] = "03483956563750341"

    # Fetch the data
    df = fetch_paginated(session, url, params, page_size=500, timeout=timeout)
    return df
