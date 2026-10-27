"""03 - Jalankan query di 03_analysis.sql, lalu hitung segmen, Pareto, repeat purchase, skenario retensi,
dan uji lima hipotesis. Semua hasil ditulis ke project/results/2-analysis/*.csv.

Input : project/project_9.duckdb (dari 02_build_db.py)
        project/results/1-data-preparation/01_cleaning_log.csv
"""
import re
import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common import DB_PATH, MIN_CUSTOMER_N, RES_ANALYSIS, RES_PREP, SQL_ANALYSIS  # noqa: E402

con = duckdb.connect(str(DB_PATH), read_only=True)


def idn(x, d=0):
    """Format angka Indonesia: 1.234,5"""
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def save(df, name):
    df.to_csv(RES_ANALYSIS / f"{name}.csv", index=False)
    return df


# --- 1. Query bernama dari file SQL
blocks = re.split(r"^-- name: ", (SQL_ANALYSIS / "03_analysis.sql").read_text(encoding="utf-8"), flags=re.M)[1:]
named = {}
for b in blocks:
    name, body = b.split("\n", 1)
    named[name.strip()] = con.sql(body).df()
    save(named[name.strip()], name.strip())

# --- 2. Periode dan jendela 12 bulan terakhir
maxd, mind = con.sql("SELECT max(invoice_ts)::DATE, min(invoice_ts)::DATE FROM transactions").fetchall()[0]
win_start = pd.Timestamp(maxd) - pd.Timedelta(days=365)
years = (pd.Timestamp(maxd) - pd.Timestamp(mind)).days / 365.25

# --- 3. Pelanggan: revenue 12 bulan terakhir dan segmen
cust = con.sql("SELECT * FROM dim_customer").df()
win = con.sql(f"""
    SELECT customer_id,
           round(sum(line_revenue), 2) AS revenue_12m,
           count(DISTINCT CASE WHEN NOT is_cancel THEN invoice_no END) AS invoices_12m
    FROM transactions
    WHERE customer_id IS NOT NULL AND invoice_ts >= TIMESTAMP '{win_start.date()}'
    GROUP BY customer_id
""").df()
cust = cust.merge(win, on="customer_id", how="left")
cust["revenue_12m"] = cust["revenue_12m"].fillna(0.0)
cust["invoices_12m"] = cust["invoices_12m"].fillna(0).astype(int)
active = cust[(cust["invoices_12m"] > 0) & (cust["revenue_12m"] > 0)].copy()
active["pct"] = active["revenue_12m"].rank(method="first", pct=True)
active["segment"] = np.select(
    [active["pct"] > 0.90, active["pct"] > 0.70, active["pct"] > 0.40],
    ["VIP", "Loyal", "Regular"], default="Light")
cust = cust.merge(active[["customer_id", "segment"]], on="customer_id", how="left")
cust["segment"] = cust["segment"].fillna("Tidak aktif 12 bulan")
cust["returning"] = cust["n_invoice"] > 1
SEG_ORDER = ["VIP", "Loyal", "Regular", "Light", "Tidak aktif 12 bulan"]

seg = (cust.groupby("segment")
       .agg(pelanggan=("customer_id", "count"),
            revenue_total=("revenue", "sum"),
            median_revenue=("revenue", "median"),
            repeat_customers=("returning", "sum"))
       .reindex(SEG_ORDER).reset_index())
seg["share_revenue"] = (seg["revenue_total"] / seg["revenue_total"].sum()).round(4)
seg["repeat_rate"] = (seg["repeat_customers"] / seg["pelanggan"]).round(4)
save(seg.round(2), "q7_segments")

# --- 4. Q6: 10% pelanggan teratas
rev_sorted = cust["revenue"].sort_values(ascending=False).reset_index(drop=True)
n_top = int(np.ceil(0.10 * len(rev_sorted)))
top_share = rev_sorted.iloc[:n_top].sum() / rev_sorted.sum()
save(pd.DataFrame([{"pelanggan_total": len(rev_sorted), "pelanggan_top10": n_top,
                    "revenue_total": round(rev_sorted.sum(), 2),
                    "revenue_top10": round(rev_sorted.iloc[:n_top].sum(), 2),
                    "share_top10": round(top_share, 4)}]), "q6_top10")

# --- 5. Q4: Pareto produk sampai 80% revenue
pr = named["q4_product_revenue"].copy()
pr = pr[pr["net_revenue"] > 0].sort_values("net_revenue", ascending=False).reset_index(drop=True)
pr["cum_share"] = (pr["net_revenue"].cumsum() / pr["net_revenue"].sum()).round(4)
n80 = int((pr["cum_share"] < 0.80).sum() + 1)
save(pr, "q4_pareto_product")
n_prod = len(pr)

# --- 6. Q8: repeat purchase rate per segmen dan per negara
cs = cust[cust["n_invoice"] > 0]
save(cs.groupby("segment").agg(pelanggan=("customer_id", "count"), repeat=("returning", "sum"))
     .reindex(SEG_ORDER).assign(repeat_rate=lambda d: (d["repeat"] / d["pelanggan"]).round(4))
     .reset_index(), "q8_repeat_segment")
ctry = (cs.groupby("country").agg(pelanggan=("customer_id", "count"), repeat=("returning", "sum"))
        .reset_index())
ctry = ctry[ctry["pelanggan"] >= MIN_CUSTOMER_N].copy()
ctry["repeat_rate"] = (ctry["repeat"] / ctry["pelanggan"]).round(4)
save(ctry.sort_values("pelanggan", ascending=False), "q8_repeat_country")

# --- 7. Q9: jarak antar pembelian (hari) pada pelanggan yang kembali
gaps = named["q9_gap_days"].merge(cust[["customer_id", "segment"]], on="customer_id")
g = gaps.groupby("segment")["gap_days"].agg(median="median", mean="mean", n="count").reindex(SEG_ORDER).dropna()
g.loc["Semua"] = [gaps["gap_days"].median(), gaps["gap_days"].mean(), len(gaps)]
save(g.round(1).reset_index().rename(columns={"index": "segmen"}), "q9_gap_summary")
first_gap = (gaps.sort_values("ts").groupby("customer_id").first()["gap_days"])

# --- 8. Q10: skenario kenaikan repeat purchase rate (estimasi)
ret = cust[cust["returning"]]
rev_ret_year = ret.groupby("segment")["revenue"].sum() / years / ret.groupby("segment")["customer_id"].count()
scen = []
for s in ["VIP", "Loyal", "Regular", "Light"]:
    n_seg = int((cust["segment"] == s).sum())
    for d in (3, 5, 10):
        scen.append({"segmen": s, "pelanggan_segmen": n_seg, "kenaikan_poin": d,
                     "pelanggan_baru_kembali": round(n_seg * d / 100, 1),
                     "revenue_per_pelanggan_kembali_per_tahun": round(float(rev_ret_year[s]), 2),
                     "tambahan_revenue_per_tahun_estimated": round(n_seg * d / 100 * float(rev_ret_year[s]), 0)})
scen = pd.DataFrame(scen)
save(scen, "q10_retention_scenarios")

# --- 9. Q11: pasangan produk (dengan nama)
dp = con.sql("SELECT stock_code, description FROM dim_product").df().set_index("stock_code")["description"]
pairs = named["q11_pairs"].copy()
pairs["nama_a"] = pairs["kode_a"].map(dp)
pairs["nama_b"] = pairs["kode_b"].map(dp)
save(pairs, "q11_pairs")

# --- 10. Q12: dampak pembersihan dan pembatalan terhadap revenue
log = pd.read_csv(RES_PREP / "01_cleaning_log.csv")
dibuang = log.loc[log["status"] == "dibuang", "revenue"].sum()
clean_rev = float(con.sql("SELECT sum(line_revenue) FROM transactions").fetchall()[0][0])
cancel_rev = float(con.sql("SELECT sum(line_revenue) FROM transactions WHERE is_cancel").fetchall()[0][0])
gross_rev = clean_rev - cancel_rev
impact = pd.DataFrame([
    {"ukuran": "revenue mentah (sebelum cleaning)", "nilai": round(clean_rev + dibuang, 2)},
    {"ukuran": "revenue setelah cleaning (net)", "nilai": round(clean_rev, 2)},
    {"ukuran": "revenue penjualan (tanpa batal)", "nilai": round(gross_rev, 2)},
    {"ukuran": "revenue batal (negatif)", "nilai": round(cancel_rev, 2)},
    {"ukuran": "selisih revenue mentah vs net", "nilai": round(clean_rev + dibuang - clean_rev, 2)},
])
save(impact, "q12_impact")

# --- 11. Q14: cek silang periode
save(named["q14_overlap"], "q14_overlap")

# --- 12. Uji hipotesis
season = named["q1_season"].set_index("bulan_ke")["rata_rata_revenue"]
top_m = int(season.idxmax())
h1_top3 = list(season.sort_values(ascending=False).index[:3])
h1_v = "Terbukti" if top_m in (9, 10, 11) else ("Sebagian" if any(m in (9, 10, 11) for m in h1_top3) else "Tidak terbukti")
h1_b = (f"Bulan tertinggi rata-rata: {top_m}. Tiga teratas: {h1_top3}. "
        f"Sep-Nov rata-rata £{idn(season.loc[[9, 10, 11]].mean())} vs rata-rata bulanan £{idn(season.mean())}")

sh = top_share
h2_v = "Terbukti" if sh >= 0.50 else ("Sebagian" if sh >= 0.30 else "Tidak terbukti")
h2_b = f"10% pelanggan teratas = {idn(sh * 100, 1)}% revenue"

share80 = n80 / n_prod
h3_v = "Terbukti" if share80 <= 0.20 else ("Sebagian" if share80 <= 0.35 else "Tidak terbukti")
h3_b = f"{idn(n80)} dari {idn(n_prod)} produk ({idn(share80 * 100, 1)}%) mencapai 80% revenue"

uk = named["q2_country"]
uk_rev = uk.loc[uk["country"] == "United Kingdom"].iloc[0]
non = uk.loc[uk["country"] != "United Kingdom"]
aov_uk = uk_rev["net_revenue"] / uk_rev["orders"]
aov_non = non["net_revenue"].sum() / non["orders"].sum()
cust_uk = cust[cust["country"] == "United Kingdom"]["n_invoice"].mean()
cust_non = cust[(cust["country"] != "United Kingdom") & (cust["n_invoice"] > 0)]["n_invoice"].mean()
h4_v = "Terbukti" if (cust_non < cust_uk and aov_non > aov_uk) else (
    "Sebagian" if (cust_non < cust_uk or aov_non > aov_uk) else "Tidak terbukti")
h4_b = f"Rata-rata invoice per pelanggan: UK {idn(cust_uk, 2)}, non-UK {idn(cust_non, 2)}. AOV per invoice: UK £{idn(aov_uk)}, non-UK £{idn(aov_non)}"

cust_idx = cust.set_index("customer_id")
flag = pd.Series(False, index=cust_idx.index)
flag.loc[first_gap[first_gap <= 90].index] = True
tetap = (cust_idx["n_invoice"] >= 3)
p_in = tetap[flag].mean()
p_out = tetap[~flag].mean()
h5_v = "Sebagian" if p_in > p_out else "Tidak terbukti"
h5_b = (f"Pelanggan dengan pembelian ulang <= 90 hari: {idn(p_in * 100, 1)}% berstatus tetap (>= 3 invoice), "
        f"lainnya {idn(p_out * 100, 1)}%. Hubungan ini sebagian mekanis, jadi maksimal Sebagian")

hyp = pd.DataFrame([
    {"no": "H1", "hipotesis": "Penjualan memuncak September sampai November", "verdict": h1_v, "bukti": h1_b},
    {"no": "H2", "hipotesis": "Sebagian kecil pelanggan menyumbang sebagian besar revenue", "verdict": h2_v, "bukti": h2_b},
    {"no": "H3", "hipotesis": "Sebagian kecil produk menyumbang sekitar 80% revenue", "verdict": h3_v, "bukti": h3_b},
    {"no": "H4", "hipotesis": "Pelanggan luar Inggris lebih jarang memesan tetapi nilai per pesanan lebih besar", "verdict": h4_v, "bukti": h4_b},
    {"no": "H5", "hipotesis": "Pembelian ulang dalam 90 hari pertama terkait dengan pelanggan tetap", "verdict": h5_v, "bukti": h5_b},
])
save(hyp, "03_hypothesis_tests")

# --- 13. Ringkasan untuk Report
summary = {"maxd": str(maxd), "mind": str(mind), "win_start": str(win_start.date()), "years": round(years, 3),
           "n80": n80, "n_prod": n_prod, "share80": round(share80, 4), "top_share": round(top_share, 4),
           "n_top10": n_top, "n_customers": len(cust), "n_active12": int(len(active))}
pd.Series(summary).to_csv(RES_ANALYSIS / "03_summary.csv", header=["nilai"])
print(hyp.to_string(index=False))
print(seg.to_string(index=False))
print(scen.to_string(index=False))
