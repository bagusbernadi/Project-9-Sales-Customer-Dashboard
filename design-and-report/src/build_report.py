"""Membuat design-and-report/index.html (Report Project versi 2) dari page_v1.html dan CSV hasil.

- Pane Design diambil apa adanya dari page_v1.html (dicek identik dengan sumber).
- Angka di Report berasal dari project/results/*.csv dan database (lewat helper report_lib.py), lalu diaudit.
Jalankan dari mana saja:  python design-and-report/src/build_report.py
"""
import re
import sys
from pathlib import Path

import duckdb
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PROJ = REPO / "project"
sys.path.insert(0, str(PROJ / "code"))
sys.path.insert(0, str(HERE))
from common import DB_PATH, MIN_CUSTOMER_N, RES_ANALYSIS as RA, RES_PREP as RP, RES_PRESENT as RPR  # noqa: E402
from report_lib import (D, I, OK, PART, NO, audit, bars, esc, hbars, lines, pill, qa, table, REG)  # noqa: E402,F401

R = lambda p: pd.read_csv(p)  # noqa: E731
src = (HERE / "page_v1.html").read_text(encoding="utf-8")

# ---------------------------------------------------------------- data
kpi = R(RA / "03_kpi.csv").iloc[0]
summ = pd.read_csv(RA / "03_summary.csv", index_col=0)["nilai"]
hyp = R(RA / "03_hypothesis_tests.csv")
monthly = R(RA / "q1_monthly.csv")
season = R(RA / "q1_season.csv").set_index("bulan_ke")["rata_rata_revenue"]
ctry = R(RA / "q2_country.csv")
heat = R(RA / "q3_heatmap.csv")
pareto = R(RA / "q4_pareto_product.csv")
cancel = R(RA / "q5_cancel_product.csv")
top10 = R(RA / "q6_top10.csv").iloc[0]
seg = R(RA / "q7_segments.csv")
rep_seg = R(RA / "q8_repeat_segment.csv")
rep_ctry = R(RA / "q8_repeat_country.csv")
gap = R(RA / "q9_gap_summary.csv")
scen = R(RA / "q10_retention_scenarios.csv")
pairs = R(RA / "q11_pairs.csv")
imp = R(RA / "q12_impact.csv").set_index("ukuran")["nilai"]
clog = R(RP / "01_cleaning_log.csv")
tcount = R(RP / "02_table_counts.csv")
xc = R(RA / "04_crosscheck_sql_pandas.csv")
xs = R(RA / "05_crosscheck_spreadsheet.csv")
dash = R(RPR / "07_dashboard_check.csv")
ovl = R(RA / "q14_overlap.csv").iloc[0]
seg_idx = seg.set_index("segment")
hyp_idx = hyp.set_index("no")
n_prod = int(summ["n_prod"])
n80 = int(summ["n80"])
share80 = float(summ["share80"])
top_share = float(summ["top_share"])
years = float(summ["years"])
n_cust = int(summ["n_customers"])
n_act = int(summ["n_active12"])
n_rows_clean = int(tcount.set_index("tabel").loc["transactions", "baris"])
net_rev = float(kpi["net_revenue"])
n_orders = int(kpi["orders"])
aov = float(kpi["aov_invoice"])
rep_all = float(kpi["repeat_rate_all"])
n_xc = int(xc["dibandingkan"].sum())
n_xc_same = int(xc["sama"].sum())
n_xs = int(xs["dibandingkan"].sum())
n_xs_same = int(xs["sama"].sum())
n_dash = len(dash)
n_dash_pass = int((dash["status"] == "PASS").sum())
mon_peak = int(season.idxmax())
nov_avg = float(season.loc[11])
avg_month = float(season.mean())
uk = ctry[ctry["country"] == "United Kingdom"].iloc[0]
non_uk = ctry[ctry["country"] != "United Kingdom"]
non_uk_share = 1 - float(uk["share_total"])
top_ctry = non_uk.iloc[0]
VIP5 = float(scen[(scen["segmen"] == "VIP") & (scen["kenaikan_poin"] == 5)]["tambahan_revenue_per_tahun_estimated"].iloc[0])

# dokumen per hal (lihat design-and-report) untuk bagian 2.x dan 5/6
dbc = duckdb.connect(str(DB_PATH), read_only=True)
n_gaps = int(dbc.execute("select count(*) from dim_customer where n_invoice > 1").fetchone()[0])
dbc.close()

# ---------------------------------------------------------------- bagian 1
CSV_DOC = {
    "01_cleaning_log.csv": ("Langkah pembersihan dan revenue terdampak", "Q12", RP),
    "01_dropped_rows.csv": ("Satu baris per baris yang dibuang, dengan aturannya", "Q12", RP),
    "01_profile.csv": ("Profil kolom mentah per sheet", "Q12", RP),
    "02_table_counts.csv": ("Jumlah baris 4 tabel di database", "bagian 1.2a", RP),
    "03_hypothesis_tests.csv": ("Uji lima hipotesis dengan bukti", "H1 sampai H5", RA),
    "03_kpi.csv": ("KPI utama", "bagian 1.3", RA),
    "03_summary.csv": ("Ringkasan periode dan jumlah segmen", "Q6, Q7, Q10", RA),
    "q1_monthly.csv": ("Net revenue per bulan dan YoY", "Q1", RA),
    "q1_season.csv": ("Rata-rata revenue per bulan kalender", "Q1, H1", RA),
    "q2_country.csv": ("Net revenue per negara", "Q2, H4", RA),
    "q3_heatmap.csv": ("Jumlah invoice per hari dan jam", "Q3", RA),
    "q4_pareto_product.csv": ("Pareto produk sampai 80%", "Q4, H3", RA),
    "q4_product_revenue.csv": ("Revenue per produk standar", "Q4, Q5", RA),
    "q5_cancel_product.csv": ("Tingkat batal per produk (minimal 50 baris)", "Q5", RA),
    "q6_top10.csv": ("Porsi revenue 10% pelanggan teratas", "Q6, H2", RA),
    "q7_segments.csv": ("Segmen pelanggan 12 bulan terakhir", "Q7, Q8, Q10", RA),
    "q8_repeat_country.csv": ("Repeat purchase rate per negara (min. 10 pelanggan)", "Q8", RA),
    "q8_repeat_segment.csv": ("Repeat purchase rate per segmen", "Q8", RA),
    "q9_gap_days.csv": ("Jarak hari antar invoice per pelanggan", "Q9", RA),
    "q9_gap_summary.csv": ("Median dan rata-rata jarak antar invoice", "Q9", RA),
    "q10_retention_scenarios.csv": ("Skenario kenaikan repeat rate (estimated)", "Q10", RA),
    "q11_pairs.csv": ("Pasangan produk dalam satu invoice", "Q11", RA),
    "q12_impact.csv": ("Dampak cleaning dan pembatalan terhadap revenue", "Q12", RA),
    "q14_overlap.csv": ("Cek invoice di dua sheet dan baris ganda sisa", "Q14", RA),
    "04_crosscheck_sql_pandas.csv": ("Cek silang SQL vs pandas", "Q13, Q14", RA),
    "05_crosscheck_spreadsheet.csv": ("Cek silang SQL vs LibreOffice Calc", "Q14", RA),
    "q14_excel_crosscheck.xlsx": ("Workbook cek silang dengan rumus SUMIFS", "Q14", RA),
    "dash_monthly.csv": ("Data tren dan filter dashboard (per bulan dan negara)", "Dashboard", RPR),
    "dash_products.csv": ("Data produk teratas untuk dashboard", "Dashboard", RPR),
    "dash_segments.csv": ("Data segmen untuk dashboard", "Dashboard", RPR),
    "dash_scenarios.csv": ("Data skenario untuk dashboard", "Dashboard", RPR),
    "dash_countries.csv": ("Data negara untuk dashboard", "Dashboard", RPR),
    "dash_heatmap.csv": ("Data hari dan jam untuk dashboard", "Dashboard", RPR),
    "dash_kpi.csv": ("KPI untuk dashboard", "Dashboard", RPR),
    "07_dashboard_check.csv": ("Cek silang dashboard vs SQL", "Q13", RPR),
}
present = {p.name for d in (RA, RP, RPR) for p in d.iterdir() if p.suffix in (".csv", ".xlsx")}
assert present == set(CSV_DOC), ("CSV belum terdokumentasi:", present ^ set(CSV_DOC))
rows12c = []
for name, (isi, pakai, d) in CSV_DOC.items():
    p = d / name
    n = "-" if p.suffix == ".xlsx" else I(len(pd.read_csv(p)))
    rows12c.append([f"<code>{p.relative_to(REPO)}</code>", isi, n, pakai])

rp1 = []
rp1.append('<div class="card"><h4>Tabel 1.1. Kualitas data (log cleaning)</h4>' + table(
    ["Langkah", "Status", "Baris", "Revenue (GBP)", "Catatan"],
    [[esc(r.langkah), esc(r.status), I(r.baris), I(round(r.revenue)), esc(str(r.catatan) if pd.notna(r.catatan) else "")]
     for r in clog.itertuples()]) +
    f'<p>Revenue mentah (sebelum cleaning) {I(round(imp["revenue mentah (sebelum cleaning)"]))} GBP, setelah cleaning {I(round(net_rev))} GBP. '
    f'Selisih berasal dari baris ganda dan harga nol yang dibuang.</p></div>')
rp1.append('<div class="card"><h4>Tabel 1.2a. Isi database (DuckDB)</h4>' + table(
    ["Tabel", "Isi (1 baris = …)", "Baris"],
    [["<code>transactions</code>", "Satu barang dalam satu invoice", I(n_rows_clean)],
     ["<code>dim_product</code>", "Satu kode produk", I(int(tcount.set_index('tabel').loc['dim_product', 'baris']))],
     ["<code>dim_customer</code>", "Satu pelanggan (dengan Customer ID)", I(int(tcount.set_index('tabel').loc['dim_customer', 'baris']))],
     ["<code>monthly_summary</code>", "Ringkasan satu bulan", I(int(tcount.set_index('tabel').loc['monthly_summary', 'baris']))]]) +
    '<p>Segmen pelanggan dihitung di tahap analisis dan disimpan di CSV, bukan di tabel <code>dim_customer</code>.</p></div>')
rp1.append('<div class="card"><h4>Tabel 1.2b. Cek silang hasil (Q13 dan Q14)</h4>' + table(
    ["Cek", "Tingkat", "Dibandingkan", "Sama", "Selisih maks", "Status"],
    [["SQL vs pandas", r.level, I(r.dibandingkan), I(r.sama), D(r.selisih_maks, 6), OK(r.status) if r.status == "PASS" else NO(r.status)] for r in xc.itertuples()] +
    [["SQL vs LibreOffice Calc", r.level, I(r.dibandingkan), I(r.sama), D(r.selisih_maks, 6), OK(r.status) if r.status == "PASS" else NO(r.status)] for r in xs.itertuples()] +
    [["Dashboard vs SQL (Q13)", r.cek, I(1), I(1 if r.status == "PASS" else 0), D(r.selisih, 2), OK(r.status) if r.status == "PASS" else NO(r.status)] for r in dash.itertuples()]) +
    '<p>Excel tidak tersedia di sesi. Spreadsheet yang dipakai adalah LibreOffice Calc dengan rumus <code>SUMIFS</code>. Angka Excel asli belum dicek. '
    'Cek silang SQL vs pandas membaca CSV bersih yang sama, jadi yang diuji adalah query, bukan cleaning. Dashboard menampilkan net revenue dibulatkan ke rupiah bulat.</p></div>')
rp1.append('<div class="card"><h4>Tabel 1.2c. File hasil analisis (CSV) dan pertanyaan yang dijawab</h4>' + table(
    ["File", "Isi", "Baris", "Dipakai untuk"], rows12c) + '</div>')
rp1.append('<h3>1.3 Angka kunci (KPI)</h3>')
rp1.append('<div class="card"><h4>Tabel 1.3. Angka kunci (KPI)</h4>' + table(["KPI", "Rumus ringkas", "Hasil", "Jumlah data"], [
    ["Net revenue", "jumlah line_revenue (batal negatif)", "£" + I(round(net_rev)), I(n_rows_clean)],
    ["Invoice non-batal", "jumlah invoice tanpa C", I(n_orders), I(n_orders)],
    ["AOV per invoice", "net revenue ÷ invoice", "£" + I(round(aov)), I(n_orders)],
    ["Repeat purchase rate", "pelanggan > 1 invoice ÷ pelanggan", D(rep_all * 100, 1) + "%", I(n_cust)],
    ["Revenue 10% pelanggan teratas", "top 10% ÷ total revenue pelanggan", D(top_share * 100, 1) + "%", I(int(top10["pelanggan_total"]))]]) + '</div>')

# ---------------------------------------------------------------- bagian 2
PRIO = {1: "Utama", 2: "Utama", 3: "Pendukung", 4: "Utama", 5: "Pendukung", 6: "Utama", 7: "Utama", 8: "Utama",
        9: "Pendukung", 10: "Utama", 11: "Tambahan", 12: "Utama", 13: "Utama", 14: "Pendukung"}
WARN = {1, 5, 7, 8, 10, 13, 14}
QT = {1: "Berapa revenue per bulan, bagaimana tren dan pola musimannya, misalnya menjelang Natal?",
      2: "Negara mana penyumbang revenue terbesar di luar Inggris?",
      3: "Hari dan jam berapa pesanan paling ramai?",
      4: "Produk mana saja yang menyumbang sekitar 80% revenue?",
      5: "Produk mana yang paling sering dibatalkan atau dikembalikan?",
      6: "Berapa persen revenue berasal dari 10% pelanggan teratas?",
      7: "Bagaimana pelanggan dibagi menjadi segmen nilai, dan berapa kontribusi tiap segmen?",
      8: "Berapa repeat purchase rate per segmen dan per negara?",
      9: "Berapa lama jarak rata-rata antar pembelian pada pelanggan yang kembali?",
      10: "Jika repeat purchase rate segmen tertentu naik beberapa poin, berapa tambahan revenue per tahun?",
      11: "Produk apa yang sering dibeli bersama dan cocok dijadikan paket?",
      12: "Berapa baris yang batal, tanpa Customer ID, berharga nol, atau duplikat, dan bagaimana pengaruhnya pada revenue?",
      13: "Apakah angka di dashboard sama persis dengan hasil SQL?",
      14: "Apakah data dua periode tergabung tanpa transaksi ganda?"}
cnt = {k: sum(1 for v in PRIO.values() if v == k) for k in ("Utama", "Pendukung", "Tambahan")}
top_month_name = {1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
                  9: "September", 10: "Oktober", 11: "November", 12: "Desember"}
mtop = monthly.dropna(subset=["yoy_pct"])
yoy_last = mtop.iloc[-1]
seg_vip = seg_idx.loc["VIP"]
ANS = {
    1: f"Rata-rata revenue per bulan tertinggi di {top_month_name[mon_peak]} (£{I(round(nov_avg))} per bulan kalender, dua tahun data), "
       f"dibanding rata-rata bulanan £{I(round(avg_month))}. September sampai November naik di kedua tahun. "
       f"Des 2011 hanya sampai 9 Desember, jadi YoY bulan itu tidak dipakai.",
    2: f"{top_ctry['country']} penyumbang terbesar di luar Inggris dengan £{I(round(top_ctry['net_revenue']))}. "
       f"Di luar Inggris hanya {D(non_uk_share * 100, 1)}% dari total revenue.",
    3: f"Puncak pesanan ada di hari {int(heat.sort_values('orders', ascending=False).iloc[0]['hari_ke'])} "
       f"jam {int(heat.sort_values('orders', ascending=False).iloc[0]['jam'])} (jumlah invoice non-batal). "
       f"Pola per jam dan hari ada di tabel heatmap di bagian 4 Streamlit.",
    4: f"{I(n80)} dari {I(n_prod)} produk ({D(share80 * 100, 1)}%) mencapai 80% revenue. Pareto lengkap ada di Grafik 2.2a.",
    5: f"Produk dengan tingkat batal tertinggi: {cancel.iloc[0]['description'].title()} "
       f"({D(cancel.iloc[0]['cancel_rate'] * 100, 1)}% dari {I(cancel.iloc[0]['lines'])} baris). "
       f"Hanya produk dengan minimal 50 baris, jadi jumlah kejadiannya kecil untuk sebagian produk.",
    6: f"10% pelanggan teratas ({I(int(top10['pelanggan_top10']))} dari {I(int(top10['pelanggan_total']))}) menyumbang {D(top_share * 100, 1)}% revenue pelanggan.",
    7: f"Segmen VIP ({I(int(seg_vip['pelanggan']))} pelanggan) menyumbang {D(seg_vip['share_revenue'] * 100, 0)}% revenue. "
       f"Segmen dihitung dari revenue 12 bulan terakhir data, dengan {I(n_act)} pelanggan aktif.",
    8: f"Repeat rate VIP {D(rep_seg.set_index('segment').loc['VIP', 'repeat_rate'] * 100, 1)}% dan Light "
       f"{D(rep_seg.set_index('segment').loc['Light', 'repeat_rate'] * 100, 1)}%. Negara dengan minimal {MIN_CUSTOMER_N} pelanggan: "
       f"UK {D(rep_ctry.set_index('country').loc['United Kingdom', 'repeat_rate'] * 100, 1)}%. "
       f"Repeat rate tinggi di segmen atas kemungkinan karena segmen dibuat dari revenue, bukan dari jumlah invoice.",
    9: f"Median jarak antar invoice {I(int(gap.set_index(gap.columns[0]).loc['Semua', 'median']))} hari untuk semua pelanggan yang kembali. "
       f"VIP {I(int(gap.set_index(gap.columns[0]).loc['VIP', 'median']))} hari, Light {I(int(gap.set_index(gap.columns[0]).loc['Light', 'median']))} hari.",
    10: f"Tambahan revenue estimasi per tahun jika repeat VIP naik 5 poin: £{I(round(VIP5))}. "
        f"Ini estimasi dari asumsi, bukan hasil eksperimen.",
    11: f"Pasangan teratas: {pairs.iloc[0]['nama_a'].title()} dan {pairs.iloc[0]['nama_b'].title()} ({I(pairs.iloc[0]['invoices'])} invoice). "
        f"Cocok sebagai paket setelah uji A/B.",
    12: f"{I(int(clog.loc[clog['langkah'].str.startswith('duplikat'), 'baris'].iloc[0]))} baris ganda, "
        f"{I(int(clog.loc[clog['langkah'].str.startswith('harga'), 'baris'].iloc[0]))} harga nol atau negatif, "
        f"{I(int(clog.loc[clog['langkah'].str.startswith('baris batal'), 'baris'].iloc[0]))} baris batal, dan "
        f"{I(int(clog.loc[clog['langkah'].str.startswith('baris tanpa Customer'), 'baris'].iloc[0]))} baris tanpa Customer ID. "
        f"Revenue batal £{I(round(abs(imp['revenue batal (negatif)'])))} mengurangi net revenue.",
    13: f"Dashboard dan SQL sama untuk {n_dash_pass} dari {n_dash} cek (net revenue dibulatkan ke rupiah bulat). Dashboard dibuat di Streamlit, bukan Looker Studio.",
    14: f"{I(int(ovl['invoice_di_dua_sheet_setelah_cleaning']))} invoice masih muncul di dua sheet setelah cleaning dan "
        f"{I(int(ovl['baris_duplikat_sisa']))} pasang baris hanya berbeda pada deskripsi. Keduanya dibiarkan dan dicatat, karena tidak bisa dipastikan sebagai ganda.",
}
qlist = [qa(f"Q{n}", QT[n], PRIO[n], ANS[n], "Terjawab dengan catatan" if n in WARN else "Terjawab", n in WARN)
         .replace('<div class="qa', f'<div id="q{n}" class="qa', 1) for n in range(1, 15)]
warn_list = ", ".join(f"Q{n}" for n in sorted(WARN))
rp2 = ['<div class="callout g"><h4>Jawaban singkat</h4>',
       f'Semua {len(ANS)} pertanyaan dijawab dengan data. Per prioritas: Utama {cnt["Utama"]}, Pendukung {cnt["Pendukung"]}, '
       f'Tambahan {cnt["Tambahan"]}. Dijawab dengan catatan (kuning): {warn_list} ({len(WARN)} pertanyaan). '
       f'Pertanyaan utama project dijawab di bagian 7.</div>',
       '<div class="qchips">' + "".join(f'<a class="qc{" w" if n in WARN else ""}" href="#q{n}" title="{esc(QT[n])}">Q{n}</a>' for n in range(1, 15)) + '</div>',
       '<p class="how">Klik nomor pertanyaan untuk melompat. Hijau = terjawab, kuning = terjawab dengan catatan.</p>']
rp2.append('<h3>2.1 Penjualan (Q1 sampai Q3)</h3>')
rp2.append(qlist[0] + qlist[1] + qlist[2])
rp2.append('<h4>Grafik 2.1a. Net revenue per bulan (ribu GBP)</h4>' + lines(
    [m[-5:] for m in monthly["bulan"]],
    [("net revenue", "#1A73E8", 2, [round(v / 1e3, 1) for v in monthly["net_revenue"]])],
    lambda v: I(round(v)), "Net revenue per bulan", h=270, bands=()))
rp2.append('<h4>Grafik 2.1b. Rata-rata revenue per bulan kalender</h4>' + bars(
    [(top_month_name[int(m)][:3], float(v), "#1A73E8" if int(m) in (9, 10, 11) else "#9AA0A6",
      f"{top_month_name[int(m)]}: £{I(round(v))}") for m, v in season.items()],
    lambda v: I(round(v / 1e3)), "Rata-rata revenue per bulan kalender", h=260, rot=0))
rp2.append('<h3>2.2 Produk (Q4 dan Q5)</h3>')
rp2.append(qlist[3] + qlist[4])
rp2.append('<h4>Grafik 2.2a. Pareto produk: 20 teratas</h4>' + hbars(
    [(d.title()[:34], float(v) / 1e3, "#1A73E8" if i < n80 else "#9AA0A6", f"{d}: £{I(round(v))}")
     for i, (d, v) in enumerate(zip(pareto["description"].head(20), pareto["net_revenue"].head(20)))],
    lambda v: I(round(v)), "Pareto produk 20 teratas", xmax=float(pareto["net_revenue"].iloc[0]) / 1e3 * 1.05))
rp2.append('<h3>2.3 Pelanggan dan retensi (Q6 sampai Q10)</h3>')
rp2.append(qlist[5] + qlist[6] + qlist[7] + qlist[8] + qlist[9])
rp2.append('<h4>Tabel 2.3a. Segmen pelanggan 12 bulan terakhir</h4>' + table(
    ["Segmen", "Pelanggan", "Revenue (GBP)", "Porsi revenue", "Repeat rate"],
    [[r.segment, I(r.pelanggan), I(round(r.revenue_total)), D(r.share_revenue * 100, 1) + "%", D(r.repeat_rate * 100, 1) + "%"]
     for r in seg.itertuples()]))
rp2.append('<h4>Tabel 2.3b. Skenario kenaikan repeat rate (estimated)</h4>' + table(
    ["Segmen", "Kenaikan (poin)", "Pelanggan kembali (perkiraan)", "Tambahan revenue per tahun (GBP)"],
    [[r.segmen, I(r.kenaikan_poin), D(r.pelanggan_baru_kembali, 1), I(round(r.tambahan_revenue_per_tahun_estimated))]
     for r in scen.itertuples() if r.kenaikan_poin == 5]))
rp2.append('<h3>2.4 Validitas data (Q11 sampai Q14)</h3>')
rp2.append(qlist[10] + qlist[11] + qlist[12] + qlist[13])
rp2.append('<h4>Tabel 2.4b. Pasangan produk paling sering dibeli bersama</h4>' + table(
    ["Produk A", "Produk B", "Invoice"],
    [[a.title(), b.title(), I(n)] for a, b, n in zip(pairs["nama_a"].head(8), pairs["nama_b"].head(8), pairs["invoices"].head(8))]))
rp2.append('<h3>Hipotesis pada Design Project</h3>')
rp2.append('<div class="scroll"><table class="rt"><tr><th>No</th><th>Hipotesis</th><th>Verdict</th><th>Bukti</th></tr>' +
           "".join(f'<tr><td>{r.no}</td><td>{esc(r.hipotesis)}</td><td>{ {"Terbukti": OK, "Sebagian": PART}.get(r.verdict, NO)(r.verdict) }</td><td>{esc(r.bukti)}</td></tr>'
                   for r in hyp.itertuples()) + '</table></div>')

# ---------------------------------------------------------------- bagian 3
rp3 = ['<div class="callout a"><h4>Sumber</h4>Online Retail II (UCI), Versi 1, tanggal akses 23 Oktober 2026. Lisensi CC BY 4.0 (dicek di halaman UCI 28 Oktober 2026). Sitasi: Chen, D. (2012). Online Retail II [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5CG6D.</div>',
       '<h3>3.1 Hipotesis pada Design Project</h3>',
       '<div class="scroll"><table class="rt"><tr><th>No</th><th>Hipotesis</th><th>Verdict</th><th>Bukti</th></tr>' +
       "".join(f'<tr><td>{r.no}</td><td>{esc(r.hipotesis)}</td><td>{ {"Terbukti": OK, "Sebagian": PART}.get(r.verdict, NO)(r.verdict) }</td><td>{esc(r.bukti)}</td></tr>'
               for r in hyp.itertuples()) + '</table></div>',
       '<h3>3.2 Rancangan dibandingkan realisasi</h3>',
       '<div class="scroll"><table class="rt"><tr><th>Rancangan</th><th>Realisasi</th><th>Verdict</th></tr>' +
       f'<tr><td>Ukuran ±1 juta baris, ±2 tahun</td><td>{I(n_rows_clean)} baris bersih, Des 2009 sampai 9 Des 2011</td><td>{OK("Sesuai")}</td></tr>'
       f'<tr><td>4 tabel data</td><td>4 tabel di DuckDB. Segmen ditambahkan di tahap analisis</td><td>{OK("Sesuai + penyesuaian")}</td></tr>'
       f'<tr><td>Sumber dan lisensi dicek sebelum dipakai</td><td>Lisensi CC BY 4.0 (dicek 28 Okt 2026). File diunggah manual oleh user</td><td>{PART("Sebagian")}</td></tr>'
       f'<tr><td>Sumber: Online Retail II (UCI)</td><td>Sumber sama, diunduh dari file yang diunggah user</td><td>{OK("Sesuai")}</td></tr>'
       '</table></div>']

# ---------------------------------------------------------------- bagian 4
rp4 = ['<div class="scroll"><table class="rt"><tr><th>Tool</th><th>Rancangan</th><th>Realisasi</th><th>Verdict</th></tr>',
       f'<tr><td>Python (pandas)</td><td>Membaca, membersihkan, dan memuat data</td><td>Dipakai untuk cleaning, cek silang, dan ekspor</td><td>{OK("Sesuai")}</td></tr>',
       f'<tr><td>DuckDB + SQL</td><td>Database dan query KPI</td><td>4 tabel dan query bernama di <code>03_analysis.sql</code></td><td>{OK("Sesuai")}</td></tr>',
       f'<tr><td>Excel (opsional)</td><td>Cek silang revenue beberapa bulan dan negara</td><td>Excel tidak tersedia di sesi. LibreOffice Calc dengan rumus SUMIFS</td><td>{PART("Sesuai + penyesuaian")}</td></tr>',
       f'<tr><td>Looker Studio</td><td>Dashboard 4 halaman, tabel ringkasan dari Google Sheets</td><td>Diganti <b>Streamlit</b> atas persetujuan user. Looker Studio butuh akun Google, dan tabel ringkasan kini dari CSV</td><td>{PART("Berubah")}</td></tr>',
       f'<tr><td>Streamlit + Plotly</td><td>Tidak ada di rancangan</td><td>Dashboard 4 tab dengan filter, diuji dengan AppTest. Belum di-deploy</td><td>{OK("Tambahan")}</td></tr>',
       f'<tr><td>matplotlib dan nbformat</td><td>Notebook dan infografik</td><td>Infografik PNG dan PDF, notebook dijalankan tanpa error</td><td>{OK("Sesuai")}</td></tr>',
       f'<tr><td>GitHub + Markdown</td><td>Repositori dan README</td><td>Repositori di branch <code>project-9-build</code></td><td>{OK("Sesuai")}</td></tr>',
       '</table></div>',
       '<div class="callout a"><h4>Catatan: dashboard Looker Studio diganti Streamlit</h4>'
       'Atas persetujuan user, dashboard dibuat dengan Streamlit (bukan Looker Studio). Rancangan pada halaman Design tidak diubah. '
       'Akibatnya, kriteria "angka di Looker Studio sama dengan SQL" dicek untuk dashboard Streamlit, dan Looker Studio tidak dibuat.</div>']

# ---------------------------------------------------------------- bagian 5
STEP_REAL = [
    ("Sesuai", OK, "<code>docs/definitions.md</code>"),
    ("Sesuai", OK, "<code>docs/data_dictionary.md</code>, 4 tabel"),
    ("Sesuai + penyesuaian", PART, "File diunggah user (unduhan dari sumber tidak tersedia di sesi). Profil di <code>01_profile.csv</code>"),
    ("Sesuai + penyesuaian", PART, "Duplikat, harga nol, spasi teks. Dua pasang ganda dibiarkan (Q14)"),
    ("Sesuai", OK, "Empat tabel dimuat ke <code>project_9.duckdb</code>"),
    ("Sesuai", OK, "Query bernama di <code>03_analysis.sql</code>"),
    ("Sesuai + penyesuaian", PART, "Excel diganti LibreOffice Calc. SQL vs pandas juga dicek"),
    ("Sesuai", OK, "Q1 sampai Q9 dan Q11 dijawab"),
    ("Sesuai", OK, "Skenario 3, 5, dan 10 poin, diberi label estimated"),
    ("Sesuai + penyesuaian", PART, "Ekspor ke CSV agregat untuk Streamlit, bukan Google Sheets"),
    ("Sebagian", PART, "Dashboard Streamlit dibuat dan diuji (Q13). Belum di-deploy"),
    ("Sesuai", OK, "README dan Report v2 selesai"),
]
steps = re.findall(r'<b class="t">(.*?)</b>', src[src.index('id="s6"'):src.index('id="s7"')])
assert len(steps) == 12, len(steps)
rp5 = ['<p class="how">Urutan langkah sama dengan rancangan. Langkah 3, 4, 7, 10, dan 11 berbeda dalam sumber atau alat.</p>',
       '<div class="scroll"><table class="rt"><tr><th>No</th><th>Rancangan</th><th>Realisasi</th><th>Verdict</th></tr>']
for i, (t, (vtxt, fn, note)) in enumerate(zip(steps, STEP_REAL), 1):
    rp5.append(f'<tr><td>{i}</td><td>{esc(re.sub("<[^>]+>", "", t))}</td><td>{note}</td><td>{fn(vtxt)}</td></tr>')
rp5.append('</table></div>')
ADJ = ["Sumber data: file diunggah user, karena unduhan dari sumber tidak tersedia di sesi. Versi dan tanggal akses dicatat.",
       "Dashboard: Looker Studio diganti Streamlit atas persetujuan user. Rancangan Design tidak diubah, catatan ada di bagian 4.",
       "Cleaning: duplikat persis dibuang, harga nol dibuang, spasi teks dihapus. Dua pasang ganda dengan deskripsi berbeda dibiarkan.",
       "Segmen pelanggan dihitung di tahap analisis dari revenue 12 bulan terakhir, bukan dari tabel rancangan.",
       "Cek silang Excel diganti LibreOffice Calc. Hasilnya sama dengan SQL (Q14).",
       "Batas persentil segmen (10%, 30%, 60%) dan ambang hipotesis adalah asumsi, dicatat di <code>docs/definitions.md</code>, belum diuji sensitivitasnya."]
rp5.append('<div class="card"><h4>Penyesuaian dan improvisasi yang tidak ada di rancangan</h4><ul>' +
           "".join(f"<li>{x}</li>" for x in ADJ) + '</ul></div>')
FILES = [
    ("index.html", "<code>design-and-report/index.html</code>", REPO / "design-and-report/index.html", False),
    ("docs/kpi_definitions.md", "<code>project/docs/kpi_definitions.md</code> (merujuk ke definitions.md)", PROJ / "docs/kpi_definitions.md", False),
    ("docs/data_dictionary.md", "<code>project/docs/data_dictionary.md</code>", PROJ / "docs/data_dictionary.md", False),
    ("data/README.md", "<code>project/data/README.md</code>", PROJ / "data/README.md", False),
    ("data/raw/online_retail_II.xlsx", "<code>project/data/raw/online_retail_II.xlsx</code>", PROJ / "data/raw/online_retail_II.xlsx", True),
    ("scripts/clean_load.py", "<code>project/code/1-data-preparation/python/01_clean.py</code> dan <code>02_build_db.py</code>", PROJ / "code/1-data-preparation/python/01_clean.py", False),
    ("outputs/cleaning_log.csv", "<code>project/results/1-data-preparation/01_cleaning_log.csv</code>", RP / "01_cleaning_log.csv", False),
    ("retail.duckdb", "<code>project/project_9.duckdb</code>", PROJ / "project_9.duckdb", True),
    ("requirements.txt", "<code>project/requirements.txt</code>", PROJ / "requirements.txt", False),
    ("sql/", "<code>project/code/1-data-preparation/sql/</code> dan <code>project/code/2-analysis/sql/</code>", PROJ / "code/2-analysis/sql", False),
    ("notebooks/analysis.ipynb", "<code>project/results/3-presentation/analysis.ipynb</code>", RPR / "analysis.ipynb", False),
    ("outputs/crosscheck.xlsx", "<code>project/results/2-analysis/q14_excel_crosscheck.xlsx</code>", RA / "q14_excel_crosscheck.xlsx", False),
    ("outputs/retention_scenarios.csv", "<code>project/results/2-analysis/q10_retention_scenarios.csv</code>", RA / "q10_retention_scenarios.csv", False),
    ("scripts/export_looker.py", "<code>project/code/3-presentation/python/06_dashboard_data.py</code> (ekspor untuk Streamlit)", PROJ / "code/3-presentation/python/06_dashboard_data.py", False),
    ("outputs/looker_sources/", "<code>project/results/3-presentation/dash_*.csv</code>", RPR / "dash_kpi.csv", False),
    ("dashboard/app.py", "<code>project/code/3-presentation/streamlit/app.py</code> (Streamlit, bukan Looker Studio)", PROJ / "code/3-presentation/streamlit/app.py", False),
    ("dashboard/README.md", "Tidak dibuat. Cara menjalankan ada di README utama", None, False),
    ("outputs/one_sheet.pdf/.png", "<code>project/results/3-presentation/infographic.pdf</code> dan <code>.png</code>", RPR / "infographic.pdf", False),
    ("README.md", "<code>README.md</code>", REPO / "README.md", False),
    ("slides/", "Belum dibuat (opsional)", None, False),
]


def _st(path, ign):
    if path is None or not path.exists():
        return "Belum ada"
    return "Tidak di-commit" if ign else "Ada"


FSTAT = [(a, b, _st(c, d)) for a, b, c, d in FILES]
STAT_PILL = {"Ada": OK, "Belum ada": NO, "Tidak di-commit": PART}
rp5.append('<h4>Tabel 5.1. Perubahan nama dan lokasi file terhadap rancangan</h4>' +
           table(["Rancangan", "Realisasi"], [[f"<code>{a}</code>", b] for a, b, _ in FSTAT]))

# ---------------------------------------------------------------- bagian 6
OUTS = [("Dashboard interaktif (Streamlit)", "Utama", "Sebagian", PART, "<code>project/code/3-presentation/streamlit/app.py</code>. Belum di-deploy. Pengganti Looker Studio"),
        ("One-sheet infografik", "Utama", "Tercapai", OK, "<code>results/3-presentation/infographic.png</code> dan <code>.pdf</code>"),
        ("Database & query SQL", "Utama", "Tercapai", OK, "<code>project_9.duckdb</code> dibuat ulang dari skrip (tidak di-commit). Query di <code>sql/</code>"),
        ("Skrip cleaning & pemuat data", "Utama", "Tercapai", OK, "<code>01_clean.py</code> dan <code>02_build_db.py</code>"),
        ("Notebook analisis", "Utama", "Tercapai", OK, "<code>results/3-presentation/analysis.ipynb</code>, 0 cell error"),
        ("Laporan temuan & rekomendasi", "Utama", "Tercapai", OK, "README dan Report v2"),
        ("Repositori GitHub", "Utama", "Tercapai", OK, "Branch <code>project-9-build</code>"),
        ("Slide presentasi", "Opsional", "Tidak dibuat", NO, "Opsional, belum dibuat")]
rp6 = ['<div class="scroll"><table class="rt"><tr><th>Output</th><th>Label</th><th>Status</th><th>Bukti</th></tr>' +
       "".join(f'<tr><td>{o}</td><td>{l}</td><td>{fn(s)}</td><td>{b}</td></tr>' for o, l, s, fn, b in OUTS) + '</table></div>']
rp6.append('<h4>Tabel 6.1. Daftar dokumen pada rancangan vs repositori</h4>' +
           table(["Dokumen di rancangan", "Di repositori", "Status"],
                 [[f"<code>{a}</code>", b, STAT_PILL[st](st)] for a, b, st in FSTAT]))
n_out_ok = sum(1 for o in OUTS if o[2] == "Tercapai")

# ---------------------------------------------------------------- bagian 7
crit = [("Sembilan pertanyaan Utama terjawab dengan angka dari data", "Tercapai", OK,
         "Q1, Q2, Q4, Q6, Q7, Q8, Q10, Q12, Q13 dijawab, lihat bagian 2"),
        ("Angka dashboard sama dengan SQL, dan SQL sama dengan spreadsheet", "Sebagian", PART,
         f"Dashboard = SQL: {n_dash_pass} dari {n_dash} cek. SQL = LibreOffice Calc: {I(n_xs_same)} dari {I(n_xs)}. Excel asli belum"),
        ("Setiap baris diubah atau dibuang tercatat, dan tidak ada transaksi ganda", "Sebagian", PART,
         f"Log lengkap di <code>01_dropped_rows.csv</code>. {I(int(ovl['baris_duplikat_sisa']))} pasang ganda sisa dibiarkan"),
        ("Orang awam paham dashboard dalam satu menit", "Belum diuji", NO, "Dashboard tersedia, belum diuji pembaca awam"),
        ("Checklist standar terpenuhi", "Sebagian", PART, "Dashboard belum di-deploy. Excel asli belum dicek")]
n_crit_ok = sum(1 for c in crit if c[1] == "Tercapai")
n_out_done = n_out_ok
rp7 = ['<h4>7.1 Hasil analisis</h4>',
       f'<p>Revenue bersih £{I(round(net_rev))} dari {I(n_orders)} invoice. Revenue terkonsentrasi: 10% pelanggan teratas menyumbang '
       f'{D(top_share * 100, 1)}%, dan {I(n80)} dari {I(n_prod)} produk menyumbang 80%. Musim puncak ada di September sampai November. '
       f'Pelanggan luar Inggris punya nilai per invoice lebih tinggi, tetapi frekuensinya tidak lebih rendah.</p>',
       '<h4>7.2 Impact</h4>',
       f'<p>Di segmen VIP, kenaikan repeat rate 5 poin diperkirakan menambah sekitar £{I(round(VIP5))} revenue per tahun (estimated). '
       'Angka ini dari asumsi dan belum diuji dengan A/B test.</p>',
       '<h4>7.3 Success criteria</h4>',
       table(["Kriteria", "Status", "Bukti"], [[c[0], c[2](c[1]), c[3]] for c in crit]) +
       f'<p>Hasil: {I(n_crit_ok)} dari {I(len(crit))} kriteria tercapai.</p>',
       '<h4>7.4 Rekomendasi</h4>',
       '<ul><li>Fokuskan program retensi pada segmen VIP dan Loyal, lalu uji dengan A/B test.</li>'
       '<li>Pakai median dan rata-rata bersama, karena sebagian kecil pelanggan mendominasi revenue.</li>'
       '<li>Cek pembelian ulang di negara selain Inggris sebelum mengalokasikan promosi.</li></ul>',
       '<h4>7.5 Saran perbaikan</h4>',
       '<ul><li>Deploy dashboard Streamlit, lalu uji dengan pembaca awam.</li>'
       '<li>Cek silang Q14 dengan Excel asli.</li>'
       '<li>Tentukan dua pasang ganda sisa dengan pemilik data.</li></ul>',
       '<h4>7.6 Batasan</h4>',
       '<ul><li>Data hanya menggambarkan toko di dataset ini.</li>'
       '<li>Data berhenti 9 Desember 2011. Des 2011 parsial.</li>'
       '<li>Pola belum tentu penyebab. Repeat rate tinggi di segmen atas sebagian karena segmen dibuat dari revenue.</li>'
       '<li>Batas persentil segmen dan ambang hipotesis adalah asumsi. Belum diuji sensitivitasnya.</li>'
       '<li>Dua pasang baris dengan deskripsi berbeda tidak bisa dipastikan sebagai ganda. Dibiarkan.</li>'
       '<li>Dashboard belum di-deploy. Looker Studio tidak dibuat, diganti Streamlit.</li>'
       '<li>Excel asli belum dicek.</li>'
       f'<li>Analisis negara hanya untuk negara dengan minimal {MIN_CUSTOMER_N} pelanggan ({I(int(rep_ctry.shape[0]))} negara).</li></ul>']

# ---------------------------------------------------------------- rakit halaman
REPORT_HEAD = [
    ("rp1", "1. Data yang berhasil didapatkan", "Isi data mentah, tabel di database, dan data hasil analisis", rp1),
    ("rp2", "2. Apakah business question terjawab?", f"{len(ANS)} pertanyaan pada Design Project, dijawab dengan data", rp2),
    ("rp3", "3. Apakah dataset sesuai dengan Design Project?", "Perbandingan rancangan dengan realisasi", rp3),
    ("rp4", "4. Apakah tools yang digunakan sesuai?", "Perbandingan rancangan dengan eksekusi", rp4),
    ("rp5", "5. Apakah alur pengerjaan sesuai dengan Design Project?", f"{len(steps)} langkah rancangan vs yang dijalankan", rp5),
    ("rp6", "6. Apakah project output tercapai?", "Output pada Design Project, bagian 7", rp6),
    ("rp7", "7. Kesimpulan", "Hasil analisis, Impact, success criteria, rekomendasi, saran perbaikan, dan batasan", rp7),
]
EVQ_VERDICT = [("Tercapai", OK, f"{I(n_rows_clean)} baris bersih dari {I(1067371)} baris mentah, dengan log per langkah."),
               ("Terjawab", OK, f"{len(ANS)} pertanyaan dijawab, {len(WARN)} dengan catatan."),
               ("Sebagian", PART, "Dataset sesuai tema. File diunggah manual, lisensi CC BY 4.0."),
               ("Sesuai + penyesuaian", PART, "Excel diganti LibreOffice Calc. Looker diganti Streamlit."),
               ("Sebagian", PART, f"{sum(1 for r in STEP_REAL if r[0] == 'Sesuai')} dari {len(STEP_REAL)} langkah sesuai penuh."),
               ("Sebagian", PART, f"{n_out_done} dari {len(OUTS)} output tercapai. Dashboard belum di-deploy."),
               ("Sebagian", PART, f"{n_crit_ok} dari {len(crit)} kriteria tercapai.")]
evq = ('<div class="evq scroll"><table class="rt"><tr><th>No</th><th>Pertanyaan evaluasi</th><th>Verdict</th><th>Ringkasan</th></tr>' +
       "".join(f'<tr><td>{i}</td><td>{esc(REPORT_HEAD[i - 1][1])}</td><td>{EVQ_VERDICT[i - 1][1](EVQ_VERDICT[i - 1][0])}</td><td>{EVQ_VERDICT[i - 1][2]}</td></tr>'
               for i in range(1, 8)) + '</table></div>')
report_pane = ['<div class="pane" id="report" data-tab="report" hidden>',
               '<div class="callout g"><h4>Report Project versi 2: evaluasi hasil terhadap Design Project</h4>'
               f'Dibuat dari {I(n_rows_clean)} baris bersih. Cek silang: {I(n_xc)} perbandingan SQL vs pandas, {I(n_xs)} perbandingan SQL vs spreadsheet, '
               f'dan {n_dash} cek dashboard. __NTOK__ angka diaudit. Angka laporan dihasilkan dari file hasil (CSV) dan database.</div>' + evq]
for id_, t, sub, body in REPORT_HEAD:
    report_pane.append(f'<h2 id="{id_}">{t}<small>{sub}</small></h2>\n' + ("".join(body) if isinstance(body, list) else body))
report_pane.append('</div>')
report_html = "\n".join(report_pane)

# nav: tombol Design dan Report berdampingan, lalu grup link
nav_old = re.search(r'<nav aria-label="Project navigation">.*?</nav>', src, re.S).group(0)
btn_d = re.search(r'<button type="button" class="tab on" data-t="design".*?</button>', nav_old, re.S).group(0)
btn_r = re.search(r'<button type="button" class="tab" data-t="report".*?</button>', nav_old, re.S).group(0)
links_d = re.search(r'<div class="links" data-tab="design">.*?</div>', nav_old, re.S).group(0)
nav_report = ('<div class="links" data-tab="report" hidden>' +
              '<a href="#rp1">Data</a><a href="#rp2">Business Questions</a><a href="#rp3">Dataset</a><a href="#rp4">Tools</a>'
              '<a href="#rp5">Alur Kerja</a><a href="#rp6">Project Output</a><a href="#rp7">Kesimpulan</a></div>')
nav_new = '<nav aria-label="Project navigation">' + btn_d + btn_r + links_d + nav_report + '</nav>'

# audit angka
STATIC = {str(i) for i in range(0, 60)} | {"50", "100", "200", "400", "1000", "1.000", "2.200", "2026", "23", "0,5", "0,25", "0,75",
                                           "1.1", "1.2", "1.3", "2.1", "2.2", "2.3", "2.4", "3.1", "3.2", "4.1", "5.1", "6.1",
                                           "7.1", "7.2", "7.3", "7.4", "7.5", "7.6", "1.2a", "1.2b", "1.2c", "2.1a", "2.1b",
                                           "2.4a", "2.4b", "2.3a", "2.3b", "5.1", "6.1", "1.067.371", "9", "11", "12",
                                           "2009", "2010", "2011", "2010-12", "2011-12", "2.021", "0,05"}
# angka dari teks CSV hipotesis dan log (sudah dicek terhadap CSV): rata-rata Sep-Nov, revenue harga nol,
# duplikat lintas sheet, persentase dan rata-rata H4/H5, serta "90" dari judul H5 dan "72" dari nama produk
STATIC |= {"1.148.588", "158.676", "22523", "31,1", "84,8", "442", "810", "6,20", "6,49", "90", "72"}
n_tok, bad = audit(report_html, STATIC)
print("token diperiksa:", n_tok, "| tidak terdaftar:", bad)
if bad:
    from report_lib import visible_text
    vt = visible_text(report_html)
    for b in bad:
        i = vt.find(b)
        print("KONTEKS", repr(b), "->", repr(vt[max(0, i - 80): i + 40]) if i >= 0 else "(tidak ditemukan)")
assert not bad, bad
report_html = report_html.replace("__NTOK__", I(n_tok))

start_design = src.index('<div class="pane" id="design"')
end_design = src.index('<div class="pane" id="report"')
design_pane = src[start_design:end_design]
pre = src[:src.index('<nav aria-label="Project navigation">')]
pre = pre.replace("</style>", (HERE / "report.css").read_text(encoding="utf-8") + "\n</style>", 1)
post = src[src.index('</main>'):]
between = src[src.index(nav_old) + len(nav_old):start_design]
html = pre + nav_new + between + design_pane + report_html + "\n" + post
assert html.count('<div class="pane" id="design"') == 1 and html.count('id="report"') == 1
assert design_pane.strip() == src[start_design:end_design].strip()
(REPO / "design-and-report" / "index.html").write_text(html, encoding="utf-8")
print("ok ditulis", len(html), "bytes")
