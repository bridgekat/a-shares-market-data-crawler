# A-Shares Market Data Crawler

Downloads historical A-shares market data from EastMoney, including daily prices, equity structures, dividends, financial reports, etc.

- The crawler scripts are adapted from [AKShare](https://github.com/akfamily/akshare) and modified to support custom request cookies.
- The parsing scripts restructure the raw data into a more consistent format. This is done on a best-effort basis: accounting standards have evolved over time, and older financial reports can be inconsistent or incomplete. Banks, insurance and securities companies have different reporting formats, further complicating the situation. So far, no higher-quality structured data sources have been known to the authors.

## Installation

```sh
python -m pip install -e .
```

## Fetching Data

> ⚠ The crawler script is likely interrupted by anti-crawling mechanism of EastMoney, requiring manual entry of CAPTCHAs.

1. Open [this example link](https://quote.eastmoney.com/concept/sz000001.html) in your **browser**.
1. Open **developer tools** (commonly by pressing `F12`).
1. Select the **network** tab and refresh the web page to capture HTTP traffic.
1. Copy [`config.example.json`](config.example.json) to `config.json`, then find any request towards `https://push2.eastmoney.com/` and paste its **request cookies** into the `cookies` object and the `ut` field from the request parameters into the `params` object.
1. Run the crawler script with `python -m a_shares_crawler` (or `python -m a_shares_crawler --config path/to/config.json`).
1. Whenever the script is interrupted by an exception like "remote end closed connection without response", refresh the web page in your **browser**, and you should be prompted by a CAPTCHA. Solve it and re-run the script to continue the download.

Data will be downloaded to the `data/` directory. The scripts skip existing files: in order to re-download, you need to manually delete all files and re-run the script.

## Restructured Data Format

### Symbol List

Example: `symbol_list.csv`

| Column | Type | Description |
|---|---|---|
| `symbol` | `str` | Stock symbol **(unique sorted index)** |
| `name` | `str` | Short name |
| `industry` | `str` | Industry or sector |
| `area` | `str` | Geographic area |
| `concepts` | `str` | Comma-separated list of associated concepts |

### Daily Prices

Example: `000001.SZ.daily_prices.csv`

| Column | Type | Description |
|---|---|---|
| `date` | `np.datetime64` | Trading date **(unique sorted index)** |
| `open` | `np.float64` | Opening price (CNY) |
| `close` | `np.float64` | Closing price (CNY) |
| `high` | `np.float64` | Highest price (CNY) |
| `low` | `np.float64` | Lowest price (CNY) |
| `amount` | `np.float64` | Transaction amount (CNY) |
| `volume` | `np.int64` | Transaction volume (shares) |

### Equity Structures

Example: `000001.SZ.equity_structures.csv`

| Column | Type | Description |
|---|---|---|
| `date` | `np.datetime64` | Effective from date, inclusive **(index)** |
| `notice_date` | `np.datetime64` | Reference notice date, inclusive (may be N/A) |
| `total_shares` | `np.int64` | Total shares |
| `circulating_shares` | `np.int64` | Circulating shares |

### Dividends

Example: `000001.SZ.dividends.csv`

| Column | Type | Description |
|---|---|---|
| `date` | `np.datetime64` | Ex-dividend date, inclusive **(index)** |
| `notice_date` | `np.datetime64` | Reference notice date, inclusive (may be N/A) |
| `share_dividends` | `np.float64` | Share dividend per share (shares) |
| `cash_dividends` | `np.float64` | Cash dividend per share (CNY) |

### Balance Sheets

Example: `000001.SZ.balance_sheets.csv`

Fixed columns:

| Column | Type | Description |
|---|---|---|
| `report_date` | `np.datetime64` | Report up to date, inclusive **(index)** |
| `notice_date` | `np.datetime64` | Reference notice date, inclusive (may be N/A) |
| `year` | `int` | Report year |
| `error` | `bool` | Whether an error has been detected in balance checking |
| `balance_sheet.*` | `np.float64` | Hierarchical financial fields (multiple columns, see below) |

To list all `balance_sheet.*` field identifiers (e.g. `balance_sheet.assets.current.cash.other`):

```python
from a_shares_crawler.types import Schema

for field_id in Schema.balance_sheet().iter_field_ids():
    print(field_id)
```

### Income Statements

Example: `000001.SZ.income_statements.csv`

Fixed columns:

| Column | Type | Description |
|---|---|---|
| `report_date` | `np.datetime64` | Report up to date, inclusive **(index)** |
| `notice_date` | `np.datetime64` | Reference notice date, inclusive (may be N/A) |
| `year` | `int` | Report year |
| `error` | `bool` | Whether an error has been detected in balance checking |
| `income_statement.*` | `np.float64` | Hierarchical financial fields (multiple columns, see below) |

To list all `income_statement.*` field identifiers (e.g. `income_statement.profit.operating.income.revenue`):

```python
from a_shares_crawler.types import Schema

for field_id in Schema.income_statement().iter_field_ids():
    print(field_id)
```

### Cash Flow Statements

Example: `000001.SZ.cash_flow_statements.csv`

Not yet implemented.
