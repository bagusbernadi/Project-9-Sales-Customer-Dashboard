-- 02 - Membuat 4 tabel dari transactions (CSV bersih). Dijalankan oleh 02_build_db.py.
-- Revenue bersih = jumlah line_revenue semua baris (baris batal bernilai negatif).

CREATE OR REPLACE TABLE transactions AS
SELECT
    invoice_no,
    CAST(invoice_ts AS TIMESTAMP) AS invoice_ts,
    stock_code,
    description,
    quantity,
    unit_price,
    line_revenue,
    customer_id,
    country,
    is_cancel,
    is_product,
    source_sheet
FROM read_csv_auto('{clean_csv}', header = true);

-- Satu produk: nama paling sering muncul untuk kode tersebut
CREATE OR REPLACE TABLE dim_product AS
SELECT
    stock_code,
    arg_max(description, n) AS description,
    bool_or(is_product) AS is_product
FROM (
    SELECT stock_code, description, is_product, count(*) AS n
    FROM transactions
    WHERE description <> ''
    GROUP BY stock_code, description, is_product
)
GROUP BY stock_code;

-- Satu pelanggan (hanya baris dengan customer_id). Segmen dihitung di tahap analisis.
CREATE OR REPLACE TABLE dim_customer AS
SELECT
    t.customer_id,
    arg_max(t.country, t.n_country) AS country,
    min(t.invoice_ts) AS first_order,
    max(t.invoice_ts) AS last_order,
    count(DISTINCT CASE WHEN NOT t.is_cancel THEN t.invoice_no END) AS n_invoice,
    round(sum(t.line_revenue), 2) AS revenue
FROM (
    SELECT customer_id, country, invoice_ts, invoice_no, is_cancel, line_revenue,
           count(*) OVER (PARTITION BY customer_id, country) AS n_country
    FROM transactions
    WHERE customer_id IS NOT NULL
) AS t
GROUP BY t.customer_id;

-- Ringkasan per bulan. Pembelian ulang = pelanggan aktif bulan ini yang sudah pernah beli di bulan sebelumnya.
CREATE OR REPLACE TABLE monthly_summary AS
WITH buyers AS (
    SELECT DISTINCT date_trunc('month', invoice_ts) AS month, customer_id
    FROM transactions
    WHERE customer_id IS NOT NULL AND NOT is_cancel
),
first_month AS (
    SELECT customer_id, min(month) AS first_m FROM buyers GROUP BY customer_id
),
rev AS (
    SELECT date_trunc('month', invoice_ts) AS month,
           round(sum(line_revenue), 2) AS net_revenue,
           count(DISTINCT CASE WHEN NOT is_cancel THEN invoice_no END) AS orders
    FROM transactions
    GROUP BY 1
),
act AS (
    SELECT b.month,
           count(*) AS active_customers,
           count(*) FILTER (WHERE b.month > f.first_m) AS repeat_customers
    FROM buyers b JOIN first_month f USING (customer_id)
    GROUP BY b.month
)
SELECT
    r.month,
    r.net_revenue,
    r.orders,
    coalesce(a.active_customers, 0) AS active_customers,
    round(r.net_revenue / nullif(r.orders, 0), 2) AS aov,
    round(coalesce(a.repeat_customers, 0) / nullif(a.active_customers, 0), 4) AS repeat_rate
FROM rev r LEFT JOIN act a USING (month)
ORDER BY r.month;
