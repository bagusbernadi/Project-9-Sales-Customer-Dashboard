[← Back to portfolio](https://bagusbernadi.github.io/)

# Project 9: Sales & Customer Dashboard

**Status: Design (rancangan).** Halaman rancangan ada di [`index.html`](index.html). Analisis, dashboard, dan angka hasil belum dikerjakan, sehingga bagian Analysis, Recommendation, dan Impact di bawah masih kosong.

**Tujuan:** membangun dashboard penjualan toko online yang menunjukkan tren revenue, produk terlaris, serta segmen pelanggan dan negara penyumbang revenue terbesar, sehingga anggaran promosi dan program retensi dapat difokuskan pada pelanggan dan produk yang paling berpengaruh.

| | |
|---|---|
| Kategori | E-commerce / retail |
| Tingkat | Mudah |
| Data | Dataset publik Online Retail II (UCI) |
| Tools | DuckDB + SQL, Python (pandas), Google Sheets, Looker Studio. Excel opsional |

## 1. Problem

**Pertanyaan utama:** Segmen pelanggan, negara, dan produk mana yang menyumbang revenue terbesar, dan berapa tambahan revenue jika pembelian ulang di segmen utama ditingkatkan?

Rancangan memecahnya menjadi 14 pertanyaan (9 Utama, 4 Pendukung, 1 Tambahan) dalam tema penjualan, produk, pelanggan, retensi, dampak, dan validitas data. Daftar lengkap ada di bagian 2 halaman rancangan.

## 2. Data

- Sumber data: [here](https://archive.ics.uci.edu/dataset/502/online+retail+ii) (Versi: 1, Tanggal akses: 23 Oktober 2026)
- Ukuran (perkiraan, **belum diverifikasi**): ±1 juta baris, 8 kolom, Desember 2009 sampai Desember 2011 dalam dua sheet.
- Invoice batal diawali huruf C; sebagian baris tanpa Customer ID.
- Rencana tabel: `transactions`, `dim_product`, `dim_customer`, `monthly_summary`.
- Lisensi dan sitasi: dicek di halaman sumber sebelum project dipublikasikan.
- Data mentah tidak di-commit ke repository.

## 3. Analysis

Belum dikerjakan. Rencana langkah (12 langkah, tahap A sampai D) ada di bagian 6 halaman rancangan. Semua angka nanti dihitung dari data dengan SQL dan dicek silang.

Hipotesis yang akan diuji (belum terbukti):
1. Penjualan memuncak September–November.
2. Sebagian kecil pelanggan menyumbang sebagian besar revenue.
3. Sebagian kecil produk menyumbang ±80% revenue.
4. Pelanggan luar Inggris lebih jarang memesan tapi nilai pesanannya lebih besar.
5. Pembelian ulang dalam 90 hari pertama terkait dengan pelanggan tetap.

## 4. Recommendation

Belum dikerjakan. Output yang direncanakan: prioritas promosi dan program retensi per segmen.

## 5. Impact

Belum dikerjakan. Rumus yang akan dipakai (semua hasil diberi label `estimated`):

```
Tambahan revenue = pelanggan segmen × kenaikan repeat rate × revenue per pelanggan yang kembali
```

## Batasan yang sudah diketahui

- Banyak pelanggan grosir, jadi median ditampilkan bersama rata-rata.
- Pola belum tentu penyebab; promosi perlu diuji.
- Data berhenti di Desember 2011.

## Struktur repository

```
index.html   Halaman rancangan project (bisa dibuka di browser atau lewat GitHub Pages)
README.md    Dokumen ini
```

Folder `docs/`, `data/`, `scripts/`, `sql/`, `notebooks/`, `dashboard/`, dan `outputs/` ditambahkan saat pengerjaan dimulai.
