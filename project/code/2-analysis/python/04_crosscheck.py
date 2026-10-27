"""04 - Cek silang: hitung ulang angka utama dengan pandas dari CSV bersih, lalu bandingkan dengan hasil SQL.

Input : project/data/clean/transactions_clean.csv, hasil SQL di project/results/2-analysis/
Output: project/results/2-analysis/04_crosscheck_sql_pandas.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common import CLEAN_CSV, RES_ANALYSIS  # noqa: E402

TOL = 0.01  # selisih rupiah/poundsterling yang masih dianggap sama
tx = pd.read_csv(CLEAN_CSV, parse_dates=["invoice_ts"])
tx["month"] = tx["invoice_ts"].dt.to_period("M").dt.to_timestamp()
rows = []


def add(level, n, sql_vals, pd_vals):
    diff = np.abs(np.asarray(sql_vals, dtype=float) - np.asarray(pd_vals, dtype=float))
    same = int((diff <= TOL).sum())
    rows.append({"level": level, "dibandingkan": n, "sama": same, "selisih_maks": round(float(diff.max()), 6),
                 "status": "PASS" if same == n else "FAIL"})


# 1. Revenue per bulan (SQL monthly_summary vs pandas)
q1 = pd.read_csv(RES_ANALYSIS / "q1_monthly.csv")
pm = tx.groupby("month")["line_revenue"].sum().round(2)
pm = pm.reindex(pd.to_datetime(q1["bulan"] + "-01")).values
add("net revenue per bulan", len(q1), q1["net_revenue"].values, pm)

# 2. Revenue per negara
q2 = pd.read_csv(RES_ANALYSIS / "q2_country.csv").set_index("country")
pc = tx.groupby("country")["line_revenue"].sum().round(2).reindex(q2.index).values
add("net revenue per negara", len(q2), q2["net_revenue"].values, pc)

# 3. Revenue per produk (kode produk standar)
q4 = pd.read_csv(RES_ANALYSIS / "q4_product_revenue.csv").set_index("stock_code")
pp = tx[tx["is_product"]].groupby("stock_code")["line_revenue"].sum().round(2).reindex(q4.index).values
add("net revenue per produk", len(q4), q4["net_revenue"].values, pp)

# 4. Revenue per pelanggan (dim_customer)
cust = tx[tx["customer_id"].notna()].groupby("customer_id")["line_revenue"].sum().round(2)
sql_cust = pd.read_csv(RES_ANALYSIS / "q6_top10.csv")  # ringkasan saja; cek total pelanggan dari 03_summary
summ = pd.read_csv(RES_ANALYSIS / "03_summary.csv", index_col=0)["nilai"]
add("jumlah pelanggan", 1, [float(summ["n_customers"])], [float(cust.size)])
add("total revenue pelanggan", 1, [float(sql_cust["revenue_total"].iloc[0])], [float(cust.sum().round(2))])

# 5. Total net revenue dan jumlah invoice non-batal
kpi = pd.read_csv(RES_ANALYSIS / "03_kpi.csv").iloc[0]
pd_orders = tx.loc[~tx["is_cancel"], "invoice_no"].nunique()
add("KPI total (net revenue, orders)", 2, [kpi["net_revenue"], kpi["orders"]],
    [round(tx["line_revenue"].sum(), 2), pd_orders])

out = pd.DataFrame(rows)
out.to_csv(RES_ANALYSIS / "04_crosscheck_sql_pandas.csv", index=False)
print(out.to_string(index=False))
