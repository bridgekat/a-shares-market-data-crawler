from pathlib import Path
import pandas as pd
import a_shares_crawler.utils as utils


history_dir = Path(".") / "data" / "a_shares_history"

incomes = pd.read_csv(
    history_dir / "000001.SZ.income_statements.csv",
    parse_dates=["date", "notice_date"],
    index_col="date",
)
incomes.sort_index(inplace=True)
print(incomes)

# Convert year-to-date values to annualized values.
incomes = utils.ytd_to_annualized(
    incomes,
    columns=[
        col for col in incomes.columns if col not in {"date", "notice_date", "error"}
    ],
)
print(incomes)
