import re
from typing import Optional

import numpy as np
import pandas as pd


def _parse_dividend_plan(text: str) -> tuple[float, float]:
    """Parses dividend plan string."""
    # Format: "10[送<float>][转<float>][派<float>元]..."
    pattern = re.compile(r"10(?:送(\d*\.?\d*)|转(\d*\.?\d*)|派(\d*\.?\d*)元)+")
    m = pattern.match(text)
    assert m is not None
    share_dividends = float(m.group(1) or "0") + float(m.group(2) or "0")
    cash_dividends = float(m.group(3) or "0")
    return share_dividends / 10.0, cash_dividends / 10.0


def _parse_dividend_receiver(text: str) -> bool:
    """Returns whether the dividend receivers include common shareholders."""
    # All shareholders, or all excluding particular preferred shareholders
    pattern = re.compile(r"全体股东|A股股东|(?:^|[^非])流通股股东|除")
    return text == "" or pattern.search(text) is not None


def parse_dividends(raw: Optional[pd.DataFrame]) -> pd.DataFrame:
    """Prepares the dividend history for a given A-shares stock.

    Parameters
    ----------
    raw
        The fetched dividend history raw data.

    Returns
    -------
    A DataFrame containing the following columns:

        - `date`: `np.datetime64` **(index)** - ex-dividend date, inclusive
        - `notice_date`: `np.datetime64` or N/A - reference notice date, inclusive
        - `share_dividends`: `np.float64` - share dividend per share (shares)
        - `cash_dividends`: `np.float64` - cash dividend per share (CNY)
    """

    # Filter out irrelevant entries
    if raw is not None:
        valid_mask = (
            (raw["IS_UNASSIGN"].astype(int) == 0)
            & (raw["ASSIGN_PROGRESS"] == "实施方案")
            & (raw["ASSIGN_OBJECT"].fillna("").map(_parse_dividend_receiver))
            & ~raw["EX_DIVIDEND_DATE"].isna()
            & ~raw["IMPL_PLAN_PROFILE"].isna()
        )
        raw = raw.loc[valid_mask]
        if raw.empty:
            raw = None

    # Construct dividend `DataFrame`
    if raw is not None:
        df = pd.DataFrame()
        df["date"] = pd.to_datetime(raw["EX_DIVIDEND_DATE"], format="%Y-%m-%d %H:%M:%S")
        df["notice_date"] = pd.to_datetime(
            raw["NOTICE_DATE"], format="%Y-%m-%d %H:%M:%S"
        )
        df["share_dividends"], df["cash_dividends"] = zip(
            *raw["IMPL_PLAN_PROFILE"].map(_parse_dividend_plan)
        )
        df.set_index("date", inplace=True)

    else:
        df = pd.DataFrame()
        df["date"] = pd.Series(dtype="datetime64[ns]")
        df["notice_date"] = pd.Series(dtype="datetime64[ns]")
        df["share_dividends"] = pd.Series(dtype=np.float64)
        df["cash_dividends"] = pd.Series(dtype=np.float64)
        df.set_index("date", inplace=True)

    # Check data consistency
    assert df.index.notna().to_numpy().all()
    assert (df["share_dividends"] >= 0.0).all()
    assert (df["cash_dividends"] >= 0.0).all()
    return df
