# Definisi dan asumsi

## KPI (rumus)
| KPI | Rumus | Catatan |
|---|---|---|
| Net revenue | jumlah `line_revenue` semua baris bersih (`quantity × unit_price`) | Baris batal (invoice diawali `C`) bernilai negatif sehingga mengurangi revenue |
| Invoice non-batal (orders) | jumlah `invoice_no` unik tanpa `C` | |
| AOV per invoice | net revenue ÷ orders | |
| Pelanggan | `customer_id` unik yang tidak kosong | Baris tanpa Customer ID tidak masuk analisis pelanggan |
| Repeat purchase rate | pelanggan dengan lebih dari 1 invoice ÷ semua pelanggan (segmen/negara) | Dihitung dari seluruh periode data |
| Tingkat batal per produk | baris batal ÷ semua baris produk tersebut | Hanya produk dengan minimal 50 baris |

## Segmen pelanggan (asumsi, bisa disesuaikan)
- Jendela: 12 bulan terakhir data (10 Des 2010 sampai 9 Des 2011).
- Pelanggan aktif = punya invoice non-batal dan revenue positif di jendela itu. Peringkat memakai persentil revenue jendela itu.
- VIP: persentil > 0,90 (10% teratas). Loyal: > 0,70 (10 s.d. 30%). Regular: > 0,40 (30 s.d. 60%). Light: sisanya (40% terbawah).
- Pelanggan yang tidak aktif di jendela diberi label "Tidak aktif 12 bulan" dan tidak masuk skenario.
- **Belum diuji sensitivitasnya.** Batas persentil adalah pilihan sendiri.

## Produk
- Kode produk standar: 5 digit angka dengan akhiran opsional 1–2 huruf (`PRODUCT_CODE_RE` di `common.py`).
- Kode lain (`POST`, `DOT`, `M`, `BANK CHARGES`, dan sejenisnya) adalah biaya, ongkir, atau adjustment. Tetap masuk revenue, tidak masuk analisis produk.

## Ambang hipotesis (ditetapkan sebelum melihat hasil)
| Hipotesis | Terbukti | Sebagian | Tidak terbukti |
|---|---|---|---|
| H1 Puncak Sep–Nov | bulan tertinggi rata-rata ada di 9, 10, 11 | salah satu dari 9, 10, 11 masuk 3 teratas | selain itu |
| H2 10% pelanggan teratas | ≥ 50% revenue | ≥ 30% | < 30% |
| H3 ~80% revenue dari sedikit produk | ≤ 20% produk | ≤ 35% produk | > 35% |
| H4 Non-UK jarang beli tapi nilai tinggi | rata-rata invoice non-UK lebih rendah DAN AOV non-UK lebih tinggi | salah satu | tidak keduanya |
| H5 Beli ulang 90 hari terkait pelanggan tetap | share pelanggan tetap (≥ 3 invoice) lebih tinggi pada yang beli ulang ≤ 90 hari | — | sebaliknya |

H5 diberi maksimal "Sebagian" karena jumlah invoice ikut menentukan status tetap (korelasi mekanis).

## Skenario retensi (estimated)
Tambahan revenue per tahun = pelanggan segmen × (kenaikan poin ÷ 100) × revenue per pelanggan yang kembali per tahun.
- Revenue per pelanggan kembali per tahun = revenue pelanggan kembali di segmen ÷ jumlah pelanggan kembali ÷ jumlah tahun data.
- Jumlah tahun data = selisih tanggal invoice pertama dan terakhir ÷ 365,25 (≈ 2,02).
- Asumsi: pelanggan baru yang kembali menghasilkan revenue seperti rata-rata pelanggan kembali di segmennya.
