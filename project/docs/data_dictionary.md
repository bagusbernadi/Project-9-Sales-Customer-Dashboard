# Kamus data

## transactions (satu baris per barang dalam satu invoice)
| Kolom | Tipe | Arti |
|---|---|---|
| invoice_no | text | Nomor invoice. Diawali `C` = batal |
| invoice_ts | timestamp | Waktu invoice (zona waktu sumber) |
| stock_code | text | Kode barang |
| description | text | Nama barang dari sumber (bisa kosong) |
| quantity | int | Jumlah (negatif pada baris batal) |
| unit_price | decimal | Harga satuan dalam GBP |
| line_revenue | decimal | quantity × unit_price, dalam GBP |
| customer_id | int (nullable) | ID pelanggan |
| country | text | Negara pelanggan |
| is_cancel | bool | Baris batal |
| is_product | bool | Kode produk standar |
| source_sheet | text | Sheet asal |

## dim_product (satu produk)
stock_code, description (nama paling sering muncul), is_product.

## dim_customer (satu pelanggan)
customer_id, country (paling sering), first_order, last_order, n_invoice (invoice non-batal), revenue (net, GBP).

## monthly_summary (satu bulan)
month, net_revenue, orders, active_customers, aov, repeat_rate (pelanggan aktif bulan itu yang sudah pernah beli sebelumnya ÷ pelanggan aktif).

Satuan: semua revenue dalam GBP (pound sterling).
