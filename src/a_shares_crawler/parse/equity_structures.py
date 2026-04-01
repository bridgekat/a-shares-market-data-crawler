import re

import numpy as np
import pandas as pd


def _parse_equity_structure_reason(text: str) -> bool:
    """Returns whether the equity structure change is relevant."""
    # All recognized reasons
    pattern = re.compile(
        r"(定期报告|成立|增资|上市|拆细|回购|缩股|行权|合并|限制性股票|高管股份变动|股份性质变更|偿还对价股份|超额配售)"
    )
    return pattern.search(text) is not None


def parse_equity_structures(raw: pd.DataFrame | None) -> pd.DataFrame:
    """Prepares the equity structure history for a given A-shares stock.

    Parameters
    ----------
    raw
        The fetched equity structure history raw data.

    Returns
    -------
    A DataFrame containing the following columns:

        - `date`: `np.datetime64` **(index)** - effective from date, inclusive
        - `notice_date`: `np.datetime64` or N/A - reference notice date, inclusive
        - `total_shares`: `np.int64` - total shares
        - `circulating_shares`: `np.int64` - circulating shares
    """

    # Filter out irrelevant entries
    if raw is not None:
        valid_mask = (
            (raw["CHANGE_REASON"].fillna("").map(_parse_equity_structure_reason))
            & ~raw["END_DATE"].isna()
            & ~raw["TOTAL_SHARES"].isna()
            & (~raw["LISTED_A_SHARES"].isna() | ~raw["UNLIMITED_SHARES"].isna())
        )
        raw = raw.loc[valid_mask]
        if raw.empty:
            raw = None

    # Construct equity structure `DataFrame`
    if raw is not None:
        df = pd.DataFrame()
        df["date"] = pd.to_datetime(raw["END_DATE"], format="%Y-%m-%d %H:%M:%S")
        df["notice_date"] = pd.to_datetime(
            raw["NOTICE_DATE"], format="%Y-%m-%d %H:%M:%S"
        )
        df["total_shares"] = raw["TOTAL_SHARES"].astype(np.int64)
        df["circulating_shares"] = (
            raw["LISTED_A_SHARES"].fillna(raw["UNLIMITED_SHARES"]).astype(np.int64)
        )
        df.set_index("date", inplace=True)

    else:
        df = pd.DataFrame()
        df["date"] = pd.Series(dtype="datetime64[ns]")
        df["notice_date"] = pd.Series(dtype="datetime64[ns]")
        df["total_shares"] = pd.Series(dtype=np.int64)
        df["circulating_shares"] = pd.Series(dtype=np.int64)
        df.set_index("date", inplace=True)

    # Check data consistency
    assert df.index.notna().all()
    assert (df["circulating_shares"] >= 0).all()
    assert (df["circulating_shares"] <= df["total_shares"]).all()
    return df
