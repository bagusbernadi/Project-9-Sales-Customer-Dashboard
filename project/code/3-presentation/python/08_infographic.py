"""08 - One-sheet infografik (PNG dan PDF) dari tabel hasil analisis.

Output: project/results/3-presentation/infographic.png dan infographic.pdf
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common import RES_ANALYSIS, RES_PRESENT  # noqa: E402

kpi = pd.read_csv(RES_ANALYSIS / "03_kpi.csv").iloc[0]
monthly = pd.read_csv(RES_PRESENT / "dash_monthly.csv")
trend = monthly.groupby("bulan")["net_revenue"].sum()
ctry = pd.read_csv(RES_ANALYSIS / "q2_country.csv").head(8)
seg = pd.read_csv(RES_ANALYSIS / "q7_segments.csv")
prod = pd.read_csv(RES_PRESENT / "dash_products.csv").head(8)
scen = pd.read_csv(RES_ANALYSIS / "q10_retention_scenarios.csv")
top10 = pd.read_csv(RES_ANALYSIS / "q6_top10.csv").iloc[0]
pareto = pd.read_csv(RES_ANALYSIS / "q4_pareto_product.csv")
n80 = int((pareto["cum_share"] < 0.80).sum() + 1)

BLUE, GREY, RED = "#1A73E8", "#5F6368", "#D93025"
fig = plt.figure(figsize=(16, 11), facecolor="white")
fig.suptitle("Sales & Customer Dashboard: Online Retail II (Des 2009 sampai Des 2011)",
             fontsize=22, fontweight="bold", y=0.975)

# KPI
kpis = [(f"£{kpi['net_revenue'] / 1e6:,.1f} jt", "Net revenue (GBP)"),
        (f"{int(kpi['orders']):,}", "Invoice non-batal"),
        (f"£{kpi['aov_invoice']:,.0f}", "AOV per invoice"),
        (f"{top10['share_top10'] * 100:,.1f}%", "Revenue dari 10% pelanggan teratas")]
for i, (v, lab) in enumerate(kpis):
    ax = fig.add_axes([0.04 + i * 0.24, 0.84, 0.21, 0.09])
    ax.axis("off")
    ax.add_patch(plt.Rectangle((0, 0), 1, 1, transform=ax.transAxes, facecolor="#F1F3F4", edgecolor="#DADCE0"))
    ax.text(0.5, 0.62, v, ha="center", va="center", fontsize=24, fontweight="bold", color=BLUE)
    ax.text(0.5, 0.25, lab, ha="center", va="center", fontsize=12, color=GREY)

# Tren
ax = fig.add_axes([0.06, 0.45, 0.42, 0.33])
ax.plot(range(len(trend)), trend.values / 1e3, color=BLUE, lw=2.2, marker="o", ms=3)
ax.set_xticks(range(0, len(trend), 3))
ax.set_xticklabels(trend.index[::3], rotation=45, fontsize=9)
ax.set_title("Tren net revenue bulanan (ribu GBP)", loc="left", fontsize=14)
ax.grid(axis="y", alpha=0.3)
ax.spines[["top", "right"]].set_visible(False)

# Negara
ax = fig.add_axes([0.53, 0.45, 0.15, 0.33])
ax.barh(ctry["country"][::-1], ctry["net_revenue"][::-1] / 1e3, color=BLUE)
ax.set_title("8 negara teratas (ribu GBP)", loc="left", fontsize=14)
ax.tick_params(labelsize=9)
ax.spines[["top", "right"]].set_visible(False)

# Produk
ax = fig.add_axes([0.80, 0.45, 0.16, 0.33])
ax.barh(prod["description"].str.title().str[:22][::-1], prod["net_revenue"][::-1] / 1e3, color=GREY)
ax.set_title("8 produk teratas (ribu GBP)", loc="left", fontsize=14)
ax.tick_params(labelsize=8)
ax.spines[["top", "right"]].set_visible(False)

# Segmen
ax = fig.add_axes([0.06, 0.07, 0.25, 0.27])
s = seg[seg["segment"] != "Tidak aktif 12 bulan"]
ax.bar(s["segment"], s["share_revenue"] * 100, color=[BLUE, "#4285F4", "#8AB4F8", "#BDC1C6"])
for x, y in zip(s["segment"], s["share_revenue"] * 100):
    ax.text(x, y + 1, f"{y:.0f}%", ha="center", fontsize=11)
ax.set_title("Porsi revenue per segmen (12 bulan)", loc="left", fontsize=14)
ax.set_ylabel("%")
ax.spines[["top", "right"]].set_visible(False)

# Skenario
ax = fig.add_axes([0.40, 0.07, 0.25, 0.27])
sc = scen[scen["kenaikan_poin"] == 5]
ax.bar(sc["segmen"], sc["tambahan_revenue_per_tahun_estimated"] / 1e3, color=RED)
for x, y in zip(sc["segmen"], sc["tambahan_revenue_per_tahun_estimated"] / 1e3):
    ax.text(x, y + 2, f"£{y:,.0f} rb", ha="center", fontsize=11)
ax.set_title("Tambahan revenue/tahun, repeat +5 poin (estimated)", loc="left", fontsize=13)
ax.set_ylabel("ribu GBP")
ax.spines[["top", "right"]].set_visible(False)

# Pesan
ax = fig.add_axes([0.70, 0.05, 0.28, 0.27])
ax.axis("off")
msgs = [
    f"{n80:,} dari {len(pareto):,} produk menyumbang 80% revenue.",
    f"Segmen VIP ({int(s.loc[s['segment'] == 'VIP', 'pelanggan'].iloc[0])} pelanggan) menyumbang "
    f"{s.loc[s['segment'] == 'VIP', 'share_revenue'].iloc[0] * 100:.0f}% revenue.",
    "Pelanggan luar Inggris punya nilai per invoice lebih tinggi, tetapi frekuensinya tidak lebih rendah.",
    "Angka dampak adalah estimasi dari asumsi, bukan hasil eksperimen.",
]
ax.text(0, 1.02, "Temuan utama", fontsize=15, fontweight="bold", va="top")
for i, m in enumerate(msgs):
    ax.text(0, 0.80 - i * 0.2, "• " + m, fontsize=11, va="top", wrap=True)

fig.text(0.04, 0.012, "Sumber: Online Retail II (UCI), diakses 23 Oktober 2026. Revenue bersih setelah pembatalan dan cleaning.",
         fontsize=10, color=GREY)
out = RES_PRESENT / "infographic"
fig.savefig(out.with_suffix(".png"), dpi=150)
fig.savefig(out.with_suffix(".pdf"))
print("ok", out.with_suffix(".png"))
