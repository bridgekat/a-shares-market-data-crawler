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
1. Find any request towards `https://push2.eastmoney.com/` and copy its **request cookies**, paste every key-value pair into the `REQUEST_COOKIES` dictionary at the beginning of [`a_shares_em_fetch.py`](src/a_shares_crawler/a_shares_em_fetch.py). Also copy the `ut` field from the request parameters and paste it into the `REQUEST_PARAMS` dictionary.
1. Run the crawler script with `python -m a_shares_crawler`.
1. Whenever the script is interrupted by an exception like "remote end closed connection without response", refresh the web page in your **browser**, and you should be prompted by a CAPTCHA. Solve it and re-run the script to continue the download.

Data will be downloaded to the `data/` directory. The scripts skip existing files: in order to re-download, you need to manually delete all files and re-run the script.

## Restructured Data Format

### Symbol List

Example: `symbol_list.csv`

TODO

### Daily Prices

Example: `000001.SZ.daily_prices.csv`

TODO

### Equity Structures

Example: `000001.SZ.equity_structures.csv`

TODO

### Dividends

Example: `000001.SZ.dividends.csv`

TODO

### Balance Sheets

Example: `000001.SZ.balance_sheets.csv`

TODO

### Income Statements

Example: `000001.SZ.income_statements.csv`

TODO

### Cash Flow Statements

Example: `000001.SZ.cash_flow_statements.csv`

TODO
