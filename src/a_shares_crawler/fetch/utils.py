from typing import Optional, Any

from tqdm import tqdm
import math
import requests
import pandas as pd

from ..types import Exchange, Symbol, ReportKind


def exchange_market_code(exchange: Exchange) -> int:
    match exchange:
        case Exchange.SZ:
            return 0
        case Exchange.SH:
            return 1
        case Exchange.BJ:
            return 0


def fetch_paginated(
    session: requests.Session,
    url: str,
    params: dict[str, Any],
    page_size: int,
    timeout: int,
) -> Optional[pd.DataFrame]:
    """Helper function to fetch paginated data from EastMoney."""
    assert timeout > 0

    page_params = params.copy()
    page_params["ps"] = page_size  # Page size
    page_params["p"] = 1  # Page index, 1-based

    # Fetch the first page to determine total number of entries
    r = session.get(url, params=page_params, timeout=timeout)
    rj = r.json()

    # Allow missing data
    if rj["code"] == 9201:
        return None

    entries = rj["result"]["data"]
    total = int(rj["result"]["count"])
    num_pages = math.ceil(total / page_size)
    assert num_pages == int(rj["result"]["pages"])

    # Fetch the remaining pages
    for page_index in tqdm(range(1, num_pages), leave=False):
        page_params["p"] = page_index + 1
        r = session.get(url, params=page_params, timeout=timeout)
        rj = r.json()
        entries.extend(rj["result"]["data"])

    return pd.DataFrame(entries)


def fetch_company_type(
    session: requests.Session,
    symbol: Symbol,
    timeout: int,
) -> Optional[int]:
    """Helper function to fetch the company type for a given A-shares stock."""
    assert timeout > 0

    url = "https://datacenter.eastmoney.com/securities/api/data/get"

    # No need to use the global REQUEST_PARAMS here (different domains)
    params = {}
    params["type"] = "RPT_F10_PUBLIC_COMPANYTPYE"
    params["sty"] = "ALL"
    params["filter"] = f'(SECUCODE="{symbol}")'
    params["source"] = "HSF10"
    params["client"] = "PC"
    params["v"] = "03483956563750341"

    # Fetch the data
    r = session.get(url, params=params, timeout=timeout)
    rj = r.json()
    if rj["code"] == 9201:
        return None
    company_type = int(rj["result"]["data"][0]["COMPANY_TYPE"])
    return company_type


def fetch_financial_history_raw(
    session: requests.Session,
    symbol: Symbol,
    report_kind: ReportKind,
    start_date: Optional[pd.Timestamp] = None,
    end_date: Optional[pd.Timestamp] = None,
    timeout: int = 15,
) -> Optional[pd.DataFrame]:
    """Fetches the financial history for a given A-shares stock from EastMoney.

    Returns the list as a [DataFrame][pandas.DataFrame] containing the raw data.

    - Webpage: https://emweb.securities.eastmoney.com/pc_hsf10/pages/index.html?code=SZ000001#/cwfx/cwbb
    - API entry point: https://datacenter.eastmoney.com/securities/api/data/get
    """
    assert timeout > 0

    url = "https://datacenter.eastmoney.com/securities/api/data/get"
    company_type = fetch_company_type(session, symbol, timeout)

    # Determine the company type parameter
    match company_type:
        case 1:  # Securities
            char = "S"
        case 2:  # Insurance
            char = "I"
        case 3:  # Banking
            char = "B"
        case 4 | None:  # General
            char = "G"
        case _:
            raise ValueError(f"Unknown company type for {symbol:06}: {company_type}")

    # Determine the report type parameter
    match report_kind:
        case ReportKind.FINANCIAL_INDICATORS:
            params_type = f"RPT_F10_FINANCE_MAINFINADATA"
        case ReportKind.BALANCE_SHEET:
            params_type = f"RPT_F10_FINANCE_{char}BALANCE"
        case ReportKind.INCOME_STATEMENT:
            params_type = f"RPT_F10_FINANCE_{char}INCOME"
        case ReportKind.CASH_FLOW_STATEMENT:
            params_type = f"RPT_F10_FINANCE_{char}CASHFLOW"
        case _:
            raise ValueError(f"Unknown report type: {report_kind}")

    # No need to use the global REQUEST_PARAMS here (different domains)
    params = {}
    params["type"] = params_type
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
