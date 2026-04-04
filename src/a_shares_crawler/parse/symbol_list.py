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
        - `symbols.name`: `str` - short name
        - `symbols.industry`: `str` - industry or sector
        - `symbols.area`: `str` - geographic area
        - `symbols.concepts`: `str` - comma-separated list of associated concepts
    """

    df = pd.DataFrame()
    df["symbol"] = (
        raw["symbol"].astype(str).map(lambda s: str(Symbol.from_stock_str(s)))  # type: ignore
    )
    df["symbols.name"] = raw["name"].astype(str).replace({"-": ""})
    df["symbols.industry"] = raw["industry"].astype(str).replace({"-": ""})
    df["symbols.area"] = raw["area"].astype(str).replace({"-": ""})
    df["symbols.concepts"] = raw["concepts"].astype(str).replace({"-": ""})
    df.set_index("symbol", inplace=True)
    df.sort_index(inplace=True)

    # Check data consistency
    assert df.index.is_unique and df.index.is_monotonic_increasing
    return df
