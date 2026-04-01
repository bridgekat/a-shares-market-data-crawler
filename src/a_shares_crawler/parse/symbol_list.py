import pandas as pd

from ..types import Symbol


def parse_symbol_list(raw: pd.DataFrame) -> pd.DataFrame:
    """Prepares the complete list of A-shares stock symbols.

    Parameters
    ----------
    raw
        The fetched A-shares symbol list raw data.

    Returns
    -------
    A DataFrame containing the following columns:

        - `symbol`: `str` **(unique sorted index)** - stock symbol
        - `name`: `str` - short name
        - `industry`: `str` - industry or sector
        - `area`: `str` - geographic area
        - `concepts`: `str` - comma-separated list of associated concepts
    """

    df = pd.DataFrame()
    df["symbol"] = (
        raw["symbol"]
        .astype(str)
        .map(lambda s: str(Symbol.from_stock_str(s)))  # type: ignore
    )
    df["name"] = raw["name"].astype(str).replace({"-": ""})
    df["industry"] = raw["industry"].astype(str).replace({"-": ""})
    df["area"] = raw["area"].astype(str).replace({"-": ""})
    df["concepts"] = raw["concepts"].astype(str).replace({"-": ""})
    df.set_index("symbol", inplace=True)

    # Check data consistency
    assert df.index.is_unique and df.index.is_monotonic_increasing
    return df
