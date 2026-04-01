from tqdm import tqdm
import math
import requests
import pandas as pd

from ..session import REQUEST_PARAMS


def fetch_symbol_list(session: requests.Session, timeout: int = 15) -> pd.DataFrame:
    """Fetches the complete list of A-shares stock symbols from EastMoney.

    Returns the list as a [DataFrame][pandas.DataFrame] containing the raw data.

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
