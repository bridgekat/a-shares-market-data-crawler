from pathlib import Path
import pandas as pd
import a_shares_crawler.utils as utils


history_dir = Path(".") / "data" / "a_shares_history"

prices = pd.read_csv(
    history_dir / "000001.SZ.daily_prices.csv",
    parse_dates=["date"],
    index_col="date",
)

dividends = pd.read_csv(
    history_dir / "000001.SZ.dividends.csv",
    parse_dates=["date", "notice_date"],
    index_col="date",
)

# Obtain forward adjustment factors for prices.
forward_adjust = utils.forward_adjustment_factors(prices, dividends)

# Obtain backward adjustment factors for prices.
backward_adjust = forward_adjust / forward_adjust.max()

# Obtain forward-adjusted closing prices.
forward_adjusted_close = prices["prices.close"] * forward_adjust

# Obtain backward-adjusted closing prices.
backward_adjusted_close = prices["prices.close"] * backward_adjust

# Display results.
df = pd.DataFrame(
    {
        "close": prices["prices.close"],
        "forward_adjust": forward_adjust,
        "backward_adjust": backward_adjust,
        "forward_adjusted_close": forward_adjusted_close,
        "backward_adjusted_close": backward_adjusted_close,
    }
)
print(df)
