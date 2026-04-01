
import requests
import pandas as pd

from ..types import Symbol, ReportKind
from .utils import fetch_financial_history_raw


def fetch_cash_flow_statements(
    session: requests.Session,
    symbol: Symbol,
    start_date: pd.Timestamp | None = None,
    end_date: pd.Timestamp | None = None,
    timeout: int = 15,
) -> pd.DataFrame | None:
    """Fetches the cash flow statement history for a given A-shares stock from EastMoney.

    Returns the list as a [DataFrame][pandas.DataFrame] containing the raw data.
    """
    return fetch_financial_history_raw(
        session, symbol, ReportKind.CASH_FLOW_STATEMENT, start_date, end_date, timeout
    )
