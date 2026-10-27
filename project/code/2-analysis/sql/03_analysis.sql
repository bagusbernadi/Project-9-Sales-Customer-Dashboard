-- 03 - Query analisis. Setiap blok diawali "-- name: <nama>" dan hasilnya disimpan ke
-- project/results/2-analysis/<nama>.csv oleh 03_analysis.py. Segmen, uji hipotesis, dan skenario
-- ada di 03_analysis.py karena butuh persentil dan median.

-- name: 03_kpi
SELECT
    round(sum(net_revenue), 2)                                          AS net_revenue,
    sum(orders)                                                         AS orders,
    round(sum(net_revenue) / nullif(sum(orders), 0), 2)                 AS aov_invoice,
    (SELECT count(*) FROM dim_customer WHERE n_invoice > 0)             AS customers,
    (SELECT round(avg(CASE WHEN n_invoice > 1 THEN 1.0 ELSE 0 END), 4)
       FROM dim_customer WHERE n_invoice > 0)                           AS repeat_rate_all,
    (SELECT count(*) FROM transactions)                                 AS baris_transaksi
FROM monthly_summary;

-- name: q1_monthly
SELECT
    strftime(month, '%Y-%m') AS bulan,
    net_revenue,
    orders,
    aov,
    active_customers,
    repeat_rate,
    round(net_revenue / lag(net_revenue, 12) OVER (ORDER BY month) - 1, 4) AS yoy_pct,
    CASE WHEN month = DATE '2011-12-01' THEN 'parsial (sampai 9 Des 2011)' ELSE 'penuh' END AS catatan
FROM monthly_summary
ORDER BY month;

-- name: q1_season
SELECT
    extract(month FROM month)::INT AS bulan_ke,
    round(avg(net_revenue), 2)     AS rata_rata_revenue,
    count(*)                       AS jumlah_tahun
FROM monthly_summary
WHERE month < DATE '2011-12-01'
GROUP BY 1
ORDER BY 1;

-- name: q2_country
WITH tot AS (SELECT sum(line_revenue) AS t FROM transactions)
SELECT
    country,
    round(sum(line_revenue), 2)                                                   AS net_revenue,
    round(sum(line_revenue) / (SELECT t FROM tot), 4)                             AS share_total,
    count(DISTINCT CASE WHEN NOT is_cancel THEN invoice_no END)                   AS orders
FROM transactions
GROUP BY country
ORDER BY net_revenue DESC;

-- name: q3_heatmap
WITH inv AS (
    SELECT invoice_no, min(invoice_ts) AS ts
    FROM transactions
    WHERE NOT is_cancel
    GROUP BY invoice_no
)
SELECT
    extract(isodow FROM ts)::INT AS hari_ke,
    extract(hour FROM ts)::INT   AS jam,
    count(*)                     AS orders
FROM inv
GROUP BY 1, 2
ORDER BY 1, 2;

-- name: q4_product_revenue
SELECT
    t.stock_code,
    p.description,
    round(sum(t.line_revenue), 2) AS net_revenue,
    sum(t.quantity)               AS qty_net
FROM transactions t
JOIN dim_product p ON p.stock_code = t.stock_code
WHERE t.is_product
GROUP BY t.stock_code, p.description
ORDER BY net_revenue DESC;

-- name: q5_cancel_product
SELECT
    t.stock_code,
    p.description,
    count(*)                                             AS lines,
    count(*) FILTER (WHERE t.is_cancel)                  AS cancel_lines,
    round(count(*) FILTER (WHERE t.is_cancel) * 1.0 / count(*), 4) AS cancel_rate
FROM transactions t
JOIN dim_product p ON p.stock_code = t.stock_code
WHERE t.is_product
GROUP BY t.stock_code, p.description
HAVING count(*) >= 50
ORDER BY cancel_rate DESC, lines DESC;

-- name: q9_gap_days
WITH inv AS (
    SELECT customer_id, invoice_no, min(invoice_ts) AS ts
    FROM transactions
    WHERE customer_id IS NOT NULL AND NOT is_cancel
    GROUP BY customer_id, invoice_no
),
gaps AS (
    SELECT customer_id,
           date_diff('day', lag(ts) OVER (PARTITION BY customer_id ORDER BY ts), ts) AS gap_days,
           ts
    FROM inv
)
SELECT customer_id, gap_days, ts
FROM gaps
WHERE gap_days IS NOT NULL;

-- name: q11_pairs
WITH lines AS (
    SELECT DISTINCT invoice_no, stock_code
    FROM transactions
    WHERE NOT is_cancel AND is_product AND quantity > 0
)
SELECT
    a.stock_code AS kode_a,
    b.stock_code AS kode_b,
    count(*)     AS invoices
FROM lines a
JOIN lines b ON a.invoice_no = b.invoice_no AND a.stock_code < b.stock_code
GROUP BY 1, 2
ORDER BY invoices DESC
LIMIT 50;

-- name: q14_overlap
SELECT
    (SELECT count(*) FROM (SELECT invoice_no FROM transactions
                           GROUP BY invoice_no HAVING count(DISTINCT source_sheet) > 1))     AS invoice_di_dua_sheet_setelah_cleaning,
    (SELECT count(*) FROM (SELECT invoice_no, stock_code, quantity, invoice_ts, unit_price, customer_id, country,
                                  count(*) AS n
                           FROM transactions GROUP BY ALL HAVING count(*) > 1))              AS baris_duplikat_sisa;
