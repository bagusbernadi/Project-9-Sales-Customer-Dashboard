"""02 - Muat data bersih ke DuckDB dan buat 4 tabel (transactions, dim_product, dim_customer, monthly_summary).

Input : project/data/clean/transactions_clean.csv (dari 01_clean.py)
Output: project/project_9.duckdb (tidak di-commit)
        project/results/1-data-preparation/02_table_counts.csv
"""
import sys
from pathlib import Path

import duckdb
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common import CLEAN_CSV, DB_PATH, RES_PREP, SQL_PREP  # noqa: E402

sql = (SQL_PREP / "02_build_tables.sql").read_text(encoding="utf-8").replace("{clean_csv}", CLEAN_CSV.as_posix())

if DB_PATH.exists():
    DB_PATH.unlink()
con = duckdb.connect(str(DB_PATH))
con.execute(sql)

counts = []
for t in ["transactions", "dim_product", "dim_customer", "monthly_summary"]:
    counts.append({"tabel": t, "baris": con.execute(f"SELECT count(*) FROM {t}").fetchone()[0]})
pd.DataFrame(counts).to_csv(RES_PREP / "02_table_counts.csv", index=False)
con.close()
print(pd.DataFrame(counts).to_string(index=False))
