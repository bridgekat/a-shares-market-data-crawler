import numpy as np
import pandas as pd


def forward_adjustment_factors(
    prices: pd.DataFrame, dividends: pd.DataFrame
) -> pd.Series:
    """
    Calculates forward price adjustment factors from price and dividend data.
    The input prices must be indexed by trading dates, and the input dividends
    data must be indexed by ex-dividend dates (**not** notice dates).

    Returns a Series that shares the same index as `prices`.
    """
    assert prices.index.is_unique and prices.index.is_monotonic_increasing
    assert dividends.index.is_unique and dividends.index.is_monotonic_increasing

    # Extend dividends data with previous-day closing prices
    closes = prices["close"]
    closes.index += pd.Timedelta(days=1)
    closes = closes.reindex(dividends.index, method="ffill")

    # Calculate adjustment multipliers
    multipliers = 1.0 + (
        dividends["cash_dividends"] / (closes - dividends["cash_dividends"])
    ).fillna(0.0)
    multipliers *= 1.0 + dividends["share_dividends"]
    assert (multipliers >= 1.0).all()

    # Calculate forward adjustment factors
    return multipliers.cumprod().reindex(prices.index, method="ffill", fill_value=1.0)


def ytd_to_annualized(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """
    Reverts year-to-date accumulation in the specified columns of `df`.
    The input must be indexed by report dates (**not** notice dates).

    Returns a DataFrame of the same shape as `df` with the specified columns
    modified to annualized values.
    """
    assert df.index.is_unique and df.index.is_monotonic_increasing

    subtract: list[bool] = []
    duration: list[float] = []

    prev_date = None
    for date in df.index:
        assert isinstance(date, pd.Timestamp)
        if prev_date is not None and date.year == prev_date.year:
            time_delta = date - prev_date
            subtract.append(True)
            duration.append(time_delta.days / 365.0)
        else:
            time_delta = date - pd.Timestamp(year=date.year - 1, month=12, day=31)
            subtract.append(False)
            duration.append(time_delta.days / 365.0)
        prev_date = date

    subtracted = df.loc[:, columns].diff()
    df.loc[subtract, columns] = subtracted.loc[subtract, :]
    df.loc[:, columns] = df.loc[:, columns].div(duration, axis="index")
    return df
