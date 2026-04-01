from typing import Optional

import numpy as np
import pandas as pd


def parse_daily_prices(raw: Optional[pd.DataFrame]) -> pd.DataFrame:
    """Prepares the daily price history for a given A-shares stock.

    Parameters
    ----------
    raw
        The fetched daily price history raw data.

    Returns
    -------
    A DataFrame containing the following columns:

        - `date`: `np.datetime64` **(unique sorted index)** - trading date
        - `open`: `np.float64` - opening price (CNY)
        - `close`: `np.float64` - closing price (CNY)
        - `high`: `np.float64` - highest price (CNY)
        - `low`: `np.float64` - lowest price (CNY)
        - `amount`: `np.float64` - transaction amount (CNY)
        - `volume`: `np.int64` - transaction volume (shares)
    """

    # Construct price `DataFrame`
    if raw is not None:
        df = pd.DataFrame()
        df["date"] = pd.to_datetime(raw["date"], format="%Y-%m-%d")
        df["open"] = raw["open"].astype(np.float64)
        df["close"] = raw["close"].astype(np.float64)
        df["high"] = raw["high"].astype(np.float64)
        df["low"] = raw["low"].astype(np.float64)
        df["amount"] = raw["amount"].astype(np.float64)
        df["volume"] = raw["volume"].astype(np.int64) * 100  # Raw unit is 100 shares
        df.set_index("date", inplace=True)

    else:
        df = pd.DataFrame()
        df["date"] = pd.Series(dtype="datetime64[ns]")
        df["open"] = pd.Series(dtype=np.float64)
        df["close"] = pd.Series(dtype=np.float64)
        df["high"] = pd.Series(dtype=np.float64)
        df["low"] = pd.Series(dtype=np.float64)
        df["amount"] = pd.Series(dtype=np.float64)
        df["volume"] = pd.Series(dtype=np.int64)
        df.set_index("date", inplace=True)

    # Check data consistency
    assert df.index.is_unique and df.index.is_monotonic_increasing
    assert (df["low"] >= 0.0).all()
    assert (df["low"] <= df["open"]).all() and (df["open"] <= df["high"]).all()
    assert (df["low"] <= df["close"]).all() and (df["close"] <= df["high"]).all()
    assert (df["amount"] >= 0.0).all()
    assert (df["volume"] >= 0.0).all()
    return df
