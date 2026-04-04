import numpy as np
import pandas as pd


def parse_daily_prices(raw: pd.DataFrame | None) -> pd.DataFrame:
    """Prepares the daily price history for a given A-shares stock.

    Parameters
    ----------
    raw
        The fetched daily price history raw data.

    Returns
    -------
    A DataFrame containing the following columns:

        - `date`: `np.datetime64` **(unique sorted index)** - trading date
        - `prices.open`: `np.float64` - opening price (CNY)
        - `prices.close`: `np.float64` - closing price (CNY)
        - `prices.high`: `np.float64` - highest price (CNY)
        - `prices.low`: `np.float64` - lowest price (CNY)
        - `prices.amount`: `np.float64` - transaction amount (CNY)
        - `prices.volume`: `np.int64` - transaction volume (shares)
    """

    # Construct price `DataFrame`
    if raw is not None:
        df = pd.DataFrame()
        df["date"] = pd.to_datetime(raw["date"], format="%Y-%m-%d")
        df["prices.open"] = raw["open"].astype(np.float64)
        df["prices.close"] = raw["close"].astype(np.float64)
        df["prices.high"] = raw["high"].astype(np.float64)
        df["prices.low"] = raw["low"].astype(np.float64)
        df["prices.amount"] = raw["amount"].astype(np.float64)
        df["prices.volume"] = raw["volume"].astype(np.int64) * 100  # Raw unit is 100 shares
        df.set_index("date", inplace=True)
        df.sort_index(inplace=True)

    else:
        df = pd.DataFrame()
        df["date"] = pd.Series(dtype="datetime64[ns]")
        df["prices.open"] = pd.Series(dtype=np.float64)
        df["prices.close"] = pd.Series(dtype=np.float64)
        df["prices.high"] = pd.Series(dtype=np.float64)
        df["prices.low"] = pd.Series(dtype=np.float64)
        df["prices.amount"] = pd.Series(dtype=np.float64)
        df["prices.volume"] = pd.Series(dtype=np.int64)
        df.set_index("date", inplace=True)
        df.sort_index(inplace=True)

    # Check data consistency
    assert df.index.is_unique and df.index.is_monotonic_increasing
    assert (df["prices.low"] >= 0.0).all()
    assert (df["prices.low"] <= df["prices.open"]).all() and (df["prices.open"] <= df["prices.high"]).all()
    assert (df["prices.low"] <= df["prices.close"]).all() and (df["prices.close"] <= df["prices.high"]).all()
    assert (df["prices.amount"] >= 0.0).all()
    assert (df["prices.volume"] >= 0.0).all()
    return df
