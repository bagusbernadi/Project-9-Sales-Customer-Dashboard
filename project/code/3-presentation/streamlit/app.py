"""Dashboard Sales & Customer (Streamlit). Membaca tabel agregat kecil di project/results/3-presentation/.

Jalankan dari folder project/:  streamlit run code/3-presentation/streamlit/app.py
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

PRES = Path(__file__).resolve().parents[3] / "results" / "3-presentation"


@st.cache_data
def load(name):
    return pd.read_csv(PRES / f"dash_{name}.csv")


monthly, products, segments = load("monthly"), load("products"), load("segments")
scen, countries, heat, kpi = load("scenarios"), load("countries"), load("heatmap"), load("kpi")

st.set_page_config(page_title="Sales & Customer Dashboard", layout="wide")
st.title("Sales & Customer Dashboard")
st.caption("Dataset: Online Retail II (UCI), Desember 2009 sampai 9 Desember 2011. Angka revenue dalam GBP (pound sterling).")

# ---- Filter
with st.sidebar:
    st.header("Filter")
    all_c = sorted(monthly["negara"].unique())
    sel_c = st.multiselect("Negara", all_c, default=all_c)
    months = sorted(monthly["bulan"].unique())
    m_from, m_to = st.select_slider("Rentang bulan", options=months, value=(months[0], months[-1]))
    st.caption("Filter negara dan bulan berlaku di tab Ringkasan dan Negara.")

f = monthly[monthly["negara"].isin(sel_c) & monthly["bulan"].between(m_from, m_to)]
partial = "2011-12"  # Desember 2011 hanya sampai 9 Desember
note_partial = f" (Des 2011 parsial)" if m_to >= partial else ""

tab1, tab2, tab3, tab4 = st.tabs(["Ringkasan", "Produk", "Pelanggan & Segmen", "Negara"])

with tab1:
    c1, c2, c3 = st.columns(3)
    rev = f["net_revenue"].sum()
    orders = f["orders"].sum()
    c1.metric("Net revenue" + note_partial, f"£{rev:,.0f}")
    c2.metric("Invoice non-batal", f"{orders:,.0f}")
    c3.metric("AOV per invoice", f"£{(rev / orders if orders else 0):,.0f}")
    trend = f.groupby("bulan", as_index=False)[["net_revenue", "orders"]].sum()
    st.plotly_chart(px.line(trend, x="bulan", y="net_revenue", markers=True,
                            labels={"bulan": "Bulan", "net_revenue": "Net revenue (GBP)"}), width="stretch")
    st.caption("Tren revenue bulanan. Revenue batal ikut mengurangi nilai per bulan.")

with tab2:
    st.subheader("100 produk teratas berdasarkan net revenue")
    st.plotly_chart(px.bar(products.head(20), x="net_revenue", y="description", orientation="h",
                           labels={"net_revenue": "Net revenue (GBP)", "description": ""}).update_layout(
        yaxis={"categoryorder": "total ascending"}), width="stretch")
    st.dataframe(products[["description", "net_revenue", "qty_net", "cancel_rate"]].rename(columns={
        "description": "Produk", "net_revenue": "Net revenue (GBP)", "qty_net": "Qty bersih",
        "cancel_rate": "Tingkat batal"}), width="stretch", hide_index=True)
    st.caption("Tingkat batal = baris batal dibagi semua baris produk tersebut. Hanya kode produk standar.")

with tab3:
    st.subheader("Segmen pelanggan (12 bulan terakhir data)")
    st.dataframe(segments.rename(columns={"segment": "Segmen", "pelanggan": "Pelanggan",
                                          "revenue_total": "Revenue total (GBP)", "median_revenue": "Median revenue (GBP)",
                                          "share_revenue": "Porsi revenue", "repeat_rate": "Repeat rate"}),
                 width="stretch", hide_index=True)
    st.caption("Segmen dari persentil revenue 12 bulan terakhir. 'Tidak aktif 12 bulan' tidak dihitung dalam skenario.")

    st.subheader("Simulasi kenaikan repeat purchase rate")
    seg_opts = scen["segmen"].unique().tolist()
    s = st.selectbox("Segmen", seg_opts, index=0)
    d = st.slider("Kenaikan repeat purchase rate (poin)", 0, 15, 5)
    row = scen[scen["segmen"] == s].iloc[0]
    add = row["pelanggan_segmen"] * d / 100 * row["revenue_per_pelanggan_kembali_per_tahun"]
    a, b = st.columns(2)
    a.metric("Tambahan revenue per tahun (estimated)", f"£{add:,.0f}")
    b.metric("Pelanggan baru yang kembali (estimated)", f"{row['pelanggan_segmen'] * d / 100:,.1f}")
    st.caption("Estimasi = pelanggan segmen × kenaikan poin × revenue per pelanggan yang kembali per tahun. "
               "Bukan hasil eksperimen; uji dengan A/B test sebelum dipakai.")

with tab4:
    st.subheader("Negara dengan minimal 10 pelanggan")
    cc = countries[countries["country"].isin(sel_c)].sort_values("revenue", ascending=False)
    st.plotly_chart(px.bar(cc.head(15), x="country", y="revenue",
                           labels={"country": "Negara", "revenue": "Revenue (GBP)"}), width="stretch")
    st.dataframe(cc.rename(columns={"country": "Negara", "pelanggan": "Pelanggan", "revenue": "Revenue (GBP)",
                                    "repeat_rate": "Repeat rate"}), width="stretch", hide_index=True)
    st.subheader("Pola hari dan jam pesanan")
    hp = heat.copy()
    hp["hari"] = hp["hari_ke"].map({1: "Sen", 2: "Sel", 3: "Rab", 4: "Kam", 5: "Jum", 6: "Sab", 7: "Min"})
    pv = hp.pivot_table(index="hari", columns="jam", values="orders", aggfunc="sum")
    pv = pv.reindex(["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"])
    st.plotly_chart(px.imshow(pv, labels={"x": "Jam", "y": "Hari", "color": "Invoice"}), width="stretch")
