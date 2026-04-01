from typing import Optional, Any, Dict
from tqdm import tqdm
import math
import requests
import pandas as pd

from .a_shares import *


REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:146.0) Gecko/20100101 Firefox/146.0",
}

REQUEST_COOKIES = {
    # Paste your request cookies here, for example:
    "fullscreengg": "1",
    "fullscreengg2": "1",
    "gviem": "nt87XxKtlloEhsCO_5dB056e3",
    "gviem_create_time": "1775013063449",
    "nid18": "0feb665f71858cc83fdd87a70d27beee",
    "nid18_create_time": "1775013063449",
    "qgqp_b_id": "95f377294b346585c1504c0a190842dc",
    "st_asi": "delete",
    "st_inirUrl": "https://passport2.eastmoney.com/",
    "st_nvi": "OXRgM7JkxXt61pztcuV4lca6b",
    "st_psi": "20260401111102746-113200354966-0937457454",
    "st_pvi": "93641856637563",
    "st_si": "71228433700809",
    "st_sn": "95",
    "st_sp": "2025-11-22 22:39:43",
    "wsc_checkuser_ok": "1",
}

REQUEST_PARAMS: Dict[str, Any] = {
    # Paste the `ut` field from the request parameters here, for example:
    "ut": "fa5fd1943c7b386f172d6893dbfba10b",
}


def create_session() -> requests.Session:
    """
    Creates a requests session with default cookies set.
    """
    session = requests.Session()
    session.headers.update(REQUEST_HEADERS)
    session.cookies.update(REQUEST_COOKIES)

    return session


def fetch_symbol_list(session: requests.Session, timeout: int = 15) -> pd.DataFrame:
    """
    Fetches the complete list of A-shares stock symbols from EastMoney.

    Returns the list as a `DataFrame` containing the raw data.

    - Webpage: https://quote.eastmoney.com/center/gridlist.html#hs_a_board
    - API entry point: https://push2.eastmoney.com/api/qt/clist/get
    """
    assert timeout > 0

    url = "https://push2.eastmoney.com/api/qt/clist/get"

    # Copy parameters to avoid modifying the original
    params = REQUEST_PARAMS.copy()
    params["fltt"] = 2  # (?)
    params["invt"] = 2  # (?)
    params["fs"] = "m:0 t:6,m:0 t:80,m:1 t:2,m:1 t:23,m:0 t:81 s:2048"  # Filters (?)
    params["fields"] = "f12,f14,f100,f102,f103"  # Fields to fetch
    params["fid"] = "f12"  # Sort by field

    # Fetch the paginated data
    def fetch_paginated(page_size: int) -> pd.DataFrame:
        page_params = params.copy()
        page_params["np"] = 1  # Data type, 0 for object (dict), 1 for array
        page_params["pz"] = page_size  # Page size
        page_params["pn"] = 1  # Page index, 1-based
        page_params["po"] = 0  # Page ordering, 0 for ascending, 1 for descending

        # Fetch the first page to determine total number of entries
        r = session.get(url, params=page_params, timeout=timeout)
        rj = r.json()
        entries = rj["data"]["diff"]
        total = int(rj["data"]["total"])
        num_pages = math.ceil(total / page_size)

        # Fetch the remaining pages
        for page_index in tqdm(range(1, num_pages), leave=False):
            page_params["pn"] = page_index + 1
            r = session.get(url, params=page_params, timeout=timeout)
            rj = r.json()
            entries.extend(rj["data"]["diff"])

        return pd.DataFrame(entries)

    df = fetch_paginated(page_size=100)
    df.rename(
        columns={
            "f12": "symbol",
            "f14": "name",
            "f100": "industry",
            "f102": "area",
            "f103": "concepts",
        },
        inplace=True,
    )
    return df


def _exchange_market_code(exchange: Exchange) -> int:
    match exchange:
        case Exchange.SZ:
            return 0
        case Exchange.SH:
            return 1
        case Exchange.BJ:
            return 0


def fetch_daily_prices(
    session: requests.Session,
    symbol: Symbol,
    start_date: Optional[pd.Timestamp] = None,
    end_date: Optional[pd.Timestamp] = None,
    timeout: int = 15,
) -> Optional[pd.DataFrame]:
    """
    Fetches the daily price history for a given A-shares stock from EastMoney.

    Returns the list as a `DataFrame` containing the raw data.

    - Webpage: https://quote.eastmoney.com/concept/sz000001.html
    - API entry point: https://push2his.eastmoney.com/api/qt/stock/kline/get
    """
    assert timeout > 0

    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"

    # Copy parameters to avoid modifying the original
    params = REQUEST_PARAMS.copy()
    params["secid"] = (
        f"{_exchange_market_code(symbol.exchange):01}.{symbol.number:06}"  # Security ID
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


def _fetch_paginated(
    session: requests.Session,
    url: str,
    params: Dict[str, Any],
    page_size: int,
    timeout: int,
) -> Optional[pd.DataFrame]:
    """
    Helper function to fetch paginated data from EastMoney.
    """
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


def fetch_equity_structures(
    session: requests.Session,
    symbol: Symbol,
    start_date: Optional[pd.Timestamp] = None,
    end_date: Optional[pd.Timestamp] = None,
    timeout: int = 15,
) -> Optional[pd.DataFrame]:
    """
    Fetches the equity structure history for a given A-shares stock from EastMoney.

    Returns the list as a `DataFrame` containing the raw data.

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
    df = _fetch_paginated(session, url, params, page_size=500, timeout=timeout)
    return df


def fetch_dividends(
    session: requests.Session,
    symbol: Symbol,
    start_date: Optional[pd.Timestamp] = None,
    end_date: Optional[pd.Timestamp] = None,
    timeout: int = 15,
) -> Optional[pd.DataFrame]:
    """
    Fetches the dividend history for a given A-shares stock from EastMoney.

    Returns the list as a `DataFrame` containing the raw data.

    - Webpage: https://emweb.securities.eastmoney.com/pc_hsf10/pages/index.html?code=SZ000001#/fhrz
    - API entry point: https://datacenter.eastmoney.com/securities/api/data/get
    """
    assert timeout > 0

    url = "https://datacenter.eastmoney.com/securities/api/data/get"

    # No need to use the global REQUEST_PARAMS here (different domains)
    params = {}
    params["type"] = "RPT_F10_DIVIDEND_MAIN"
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
    df = _fetch_paginated(session, url, params, page_size=500, timeout=timeout)
    return df


def _fetch_company_type(
    session: requests.Session,
    symbol: Symbol,
    timeout: int,
) -> Optional[int]:
    """
    Helper function to fetch the company type for a given A-shares stock.
    """
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
    """
    Fetches the financial history for a given A-shares stock from EastMoney.

    Returns the list as a `DataFrame` containing the raw data.

    - Webpage: https://emweb.securities.eastmoney.com/pc_hsf10/pages/index.html?code=SZ000001#/cwfx/cwbb
    - API entry point: https://datacenter.eastmoney.com/securities/api/data/get
    """
    assert timeout > 0

    url = "https://datacenter.eastmoney.com/securities/api/data/get"
    company_type = _fetch_company_type(session, symbol, timeout)

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
    df = _fetch_paginated(session, url, params, page_size=500, timeout=timeout)
    return df


def fetch_balance_sheets(
    session: requests.Session,
    symbol: Symbol,
    start_date: Optional[pd.Timestamp] = None,
    end_date: Optional[pd.Timestamp] = None,
    timeout: int = 15,
) -> Optional[pd.DataFrame]:
    """
    Fetches the balance sheet history for a given A-shares stock from EastMoney.

    Returns the list as a `DataFrame` containing the raw data.
    """
    return fetch_financial_history_raw(
        session, symbol, ReportKind.BALANCE_SHEET, start_date, end_date, timeout
    )


def fetch_income_statements(
    session: requests.Session,
    symbol: Symbol,
    start_date: Optional[pd.Timestamp] = None,
    end_date: Optional[pd.Timestamp] = None,
    timeout: int = 15,
) -> Optional[pd.DataFrame]:
    """
    Fetches the income statement history for a given A-shares stock from EastMoney.

    Returns the list as a `DataFrame` containing the raw data.
    """
    return fetch_financial_history_raw(
        session, symbol, ReportKind.INCOME_STATEMENT, start_date, end_date, timeout
    )


def fetch_cash_flow_statements(
    session: requests.Session,
    symbol: Symbol,
    start_date: Optional[pd.Timestamp] = None,
    end_date: Optional[pd.Timestamp] = None,
    timeout: int = 15,
) -> Optional[pd.DataFrame]:
    """
    Fetches the cash flow statement history for a given A-shares stock from EastMoney.

    Returns the list as a `DataFrame` containing the raw data.
    """
    return fetch_financial_history_raw(
        session, symbol, ReportKind.CASH_FLOW_STATEMENT, start_date, end_date, timeout
    )


def fetch_original_reports_raw(
    session: requests.Session,
    symbol: Symbol,
    timeout: int = 15,
) -> Optional[pd.DataFrame]:
    """
    Fetches the original financial reports for a given A-shares stock from EastMoney.

    Returns the list as a `DataFrame` containing the raw data.

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
    df = _fetch_paginated(session, url, params, page_size=500, timeout=timeout)
    return df
