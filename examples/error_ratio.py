from pathlib import Path
import pandas as pd


history_dir = Path(".") / "data" / "a_shares_history"

report_types = [
    "balance_sheets",
    "income_statements",
    "cash_flow_statements",
    "indirect_statements",
]

for report_type in report_types:
    files = sorted(history_dir.glob(f"*.{report_type}.csv"))
    total = 0
    errors = 0
    for f in files:
        df = pd.read_csv(f, usecols=["error"])
        total += len(df)
        errors += df["error"].sum()
    ratio = errors / total if total else 0
    print(f"{report_type:30s}  {errors:6.0f} / {total:7d}  ({ratio:.4%})")
