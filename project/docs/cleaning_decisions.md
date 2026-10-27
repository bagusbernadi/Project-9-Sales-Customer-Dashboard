# Keputusan cleaning

1. **Dua sheet digabung.** Sheet `Year 2009-2010` dan `Year 2010-2011` digabung. Periode keduanya overlap sekitar Desember 2010.
2. **Duplikat persis dibuang** (8 kolom sama, baris pertama dipertahankan). Dari 34.335 baris, 22.523 berasal dari sheet lain (overlap) dan sisanya duplikat dalam satu sheet. Duplikat dalam sheet mungkin baris sah yang sama; keputusan ini diambil dan dicatat, dampaknya GBP 431.717 (Tabel 1.1).
   **Sisa:** 2 pasang baris dengan invoice, waktu, kode, jumlah, dan harga yang sama, tetapi deskripsi berbeda (invoice 554084 dan 575335). Dibiarkan karena tidak bisa dipastikan sebagai ganda. Dicatat di Q14.
3. **Harga nol atau negatif dibuang** (6.019 baris). Tidak bisa dipakai untuk revenue.
4. **Baris batal (invoice `C`) tidak dibuang.** Mengurangi revenue bersih.
5. **Baris tanpa Customer ID tidak dibuang.** Tetap masuk revenue, tidak masuk analisis pelanggan (229.202 baris).
6. **Kode non-produk tidak dibuang.** Tetap masuk revenue, tidak masuk analisis produk (5.889 baris).
7. **Spasi di awal atau akhir teks dihapus** (kolom Description, Country, StockCode).
