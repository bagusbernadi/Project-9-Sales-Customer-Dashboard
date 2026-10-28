[← Back to portfolio](https://bagusbernadi.github.io/)

# Project 9: Sales & Customer Dashboard

**Status: Selesai dan digabung ke `main`.** Halaman evaluasi ada di [`design-and-report/index.html`](design-and-report/index.html). Dashboard Streamlit dibuat dan diuji lokal, tetapi belum di-deploy.

**Tujuan:** membangun dashboard penjualan toko online yang menunjukkan tren revenue, produk, dan segmen pelanggan, sehingga promosi dan program retensi bisa difokuskan.

| | |
|---|---|
| Kategori | E-commerce / retail |
| Tingkat | Mudah |
| Data | Dataset publik Online Retail II (UCI) |
| Tools | DuckDB + SQL, Python (pandas), LibreOffice Calc (cek silang), Streamlit + Plotly |

## 1. Problem

**Pertanyaan utama:** Segmen pelanggan, negara, dan produk mana yang menyumbang revenue terbesar, dan berapa tambahan revenue jika pembelian ulang di segmen utama ditingkatkan?

Dipecah menjadi 14 pertanyaan (9 Utama, 4 Pendukung, 1 Tambahan). Daftar lengkap ada di bagian 2 halaman evaluasi.

## 2. Data

- Sumber data: [here](https://archive.ics.uci.edu/dataset/502/online+retail+ii) (Versi: 1, Tanggal akses: 23 Oktober 2026)
- Ukuran: 1.067.371 baris mentah, 1.027.017 baris bersih, 8 kolom, Desember 2009 sampai 9 Desember 2011.
- Cleaning: duplikat persis, harga nol, dan spasi teks. Revenue batal tetap dihitung sebagai pengurang. Aturan lengkap di `project/docs/cleaning_decisions.md`.
- Lisensi: CC BY 4.0 (dicek di halaman UCI, 28 Oktober 2026). Sitasi: Chen, D. (2012). Online Retail II [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5CG6D.
- Data mentah dan database tidak di-commit. Dibuat ulang dari skrip.

## 3. Analysis

Net revenue £19.014.209,82 dari 40.077 invoice non-batal. 10% pelanggan teratas menyumbang 63,7% revenue. 1.048 dari 4.858 produk mencapai 80% revenue.

| No | Hipotesis | Verdict |
|---|---|---|
| H1 | Penjualan memuncak September sampai November | Terbukti |
| H2 | Sebagian kecil pelanggan menyumbang sebagian besar revenue | Terbukti |
| H3 | Sebagian kecil produk menyumbang sekitar 80% revenue | Sebagian |
| H4 | Pelanggan luar Inggris lebih jarang memesan tetapi nilai per pesanan lebih besar | Sebagian |
| H5 | Pembelian ulang dalam 90 hari terkait dengan pelanggan tetap | Sebagian |

Cek silang: SQL vs pandas 100% sama (4.963 nilai), SQL vs LibreOffice Calc 100% sama, dashboard vs SQL 4 dari 4 cek lolos.

## 4. Recommendation

- Fokuskan program retensi pada segmen VIP dan Loyal, lalu uji dengan A/B test.
- Pakai median dan rata-rata bersama, karena sebagian kecil pelanggan mendominasi revenue.
- Cek pembelian ulang di negara selain Inggris sebelum mengalokasikan promosi.

## 5. Impact

Estimasi (estimated, bukan hasil eksperimen): jika repeat purchase rate segmen VIP naik 5 poin, tambahan revenue sekitar £221 ribu per tahun. Rumus dan asumsi ada di `project/docs/definitions.md`.

## Batasan

- Data hanya menggambarkan toko di dataset ini.
- Data berhenti 9 Desember 2011.
- Dashboard belum di-deploy. Rancangan menyebut Looker Studio, dan atas persetujuan user diganti Streamlit.
- Dua pasang baris dengan deskripsi berbeda tidak bisa dipastikan sebagai ganda, dan dibiarkan.
- Batas persentil segmen dan ambang hipotesis adalah asumsi, belum diuji sensitivitasnya.
- Excel asli belum dicek. Cek silang memakai LibreOffice Calc.

## Menjalankan

Dari folder `project/`, jalankan berurutan (data mentah di `project/data/raw/online_retail_II.xlsx`):

```bash
pip install -r requirements.txt
python code/1-data-preparation/python/01_clean.py
python code/1-data-preparation/python/02_build_db.py
python code/2-analysis/python/03_analysis.py
python code/2-analysis/python/04_crosscheck.py
python code/2-analysis/python/05_excel_crosscheck.py
python code/3-presentation/python/06_dashboard_data.py
python code/3-presentation/python/07_dashboard_check.py
python code/3-presentation/python/08_infographic.py
python code/3-presentation/python/09_build_notebook.py
streamlit run code/3-presentation/streamlit/app.py
```

Generator halaman: `python design-and-report/src/build_report.py` dari root repo.

## Struktur repository

```
README.md
index.html                  pengalihan ke design-and-report/
design-and-report/          index.html (tab Design + Report), src/
project/
  code/                     program
    common.py
    1-data-preparation/     python/  sql/
    2-analysis/             python/  sql/
    3-presentation/         python/  streamlit/
  results/                  hasil analisis per tahap
    1-data-preparation/  2-analysis/  3-presentation/
  data/                     raw/ (tidak di-commit), clean/ (tidak di-commit), README.md
  docs/                     definitions.md, data_dictionary.md, cleaning_decisions.md, kpi_definitions.md
  requirements.txt
```
