from typing import Optional

import requests
import pandas as pd

from ..types import Symbol, ReportKind
from .utils import fetch_financial_history_raw


def fetch_income_statements(
    session: requests.Session,
    symbol: Symbol,
    start_date: Optional[pd.Timestamp] = None,
    end_date: Optional[pd.Timestamp] = None,
    timeout: int = 15,
) -> Optional[pd.DataFrame]:
    """Fetches the income statement history for a given A-shares stock from EastMoney.

    Returns the list as a [DataFrame][pandas.DataFrame] containing the raw data.
    """
    return fetch_financial_history_raw(
        session, symbol, ReportKind.INCOME_STATEMENT, start_date, end_date, timeout
    )
