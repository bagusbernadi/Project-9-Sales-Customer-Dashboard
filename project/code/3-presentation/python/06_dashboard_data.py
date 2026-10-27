"""06 - Ekspor tabel agregat kecil untuk dashboard Streamlit (dashboard tidak membaca database 1 juta baris).

Input : project/project_9.duckdb, project/results/2-analysis/*.csv
Output: project/results/3-presentation/dash_*.csv (di-commit, ukurannya kecil)
"""
import sys
from pathlib import Path

import duckdb
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common import DB_PATH, RES_ANALYSIS, RES_PRESENT  # noqa: E402

con = duckdb.connect(str(DB_PATH), read_only=True)

# 1. Bulanan per negara (15 teratas + Lainnya), dipakai untuk tren dan filter negara
top = con.sql("""SELECT country FROM transactions GROUP BY country
                 ORDER BY sum(line_revenue) DESC LIMIT 15""").df()["country"].tolist()
monthly = con.sql(f"""
    SELECT strftime(date_trunc('month', invoice_ts), '%Y-%m') AS bulan,
           CASE WHEN country IN ({",".join("'" + c.replace("'", "''") + "'" for c in top)})
                THEN country ELSE 'Lainnya' END AS negara,
           round(sum(line_revenue), 2) AS net_revenue,
           count(DISTINCT CASE WHEN NOT is_cancel THEN invoice_no END) AS orders
    FROM transactions
    GROUP BY 1, 2
    ORDER BY 1, 2
""").df()
monthly.to_csv(RES_PRESENT / "dash_monthly.csv", index=False)

# 2. Produk: 100 teratas dengan revenue dan tingkat batal
prod = con.sql("""
    WITH r AS (
        SELECT t.stock_code, round(sum(t.line_revenue), 2) AS net_revenue, sum(t.quantity) AS qty_net,
               count(*) AS lines, count(*) FILTER (WHERE t.is_cancel) AS cancel_lines
        FROM transactions t WHERE t.is_product GROUP BY t.stock_code)
    SELECT r.stock_code, p.description, r.net_revenue, r.qty_net,
           round(r.cancel_lines * 1.0 / r.lines, 4) AS cancel_rate, r.lines
    FROM r JOIN dim_product p USING (stock_code)
    ORDER BY net_revenue DESC
    LIMIT 100
""").df()
prod.to_csv(RES_PRESENT / "dash_products.csv", index=False)

# 3. Segmen pelanggan dan skenario (dari tahap analisis)
seg = pd.read_csv(RES_ANALYSIS / "q7_segments.csv")
seg.to_csv(RES_PRESENT / "dash_segments.csv", index=False)
pd.read_csv(RES_ANALYSIS / "q10_retention_scenarios.csv").to_csv(RES_PRESENT / "dash_scenarios.csv", index=False)

# 4. Negara (pelanggan >= 10), repeat purchase rate
ctry = con.sql("""
    SELECT country, count(*) AS pelanggan,
           round(sum(revenue), 2) AS revenue,
           round(avg(CASE WHEN n_invoice > 1 THEN 1.0 ELSE 0 END), 4) AS repeat_rate
    FROM dim_customer WHERE n_invoice > 0 GROUP BY country
    HAVING count(*) >= 10
""").df()
ctry.to_csv(RES_PRESENT / "dash_countries.csv", index=False)

# 5. Pola jam dan hari, serta KPI utama
pd.read_csv(RES_ANALYSIS / "q3_heatmap.csv").to_csv(RES_PRESENT / "dash_heatmap.csv", index=False)
pd.read_csv(RES_ANALYSIS / "03_kpi.csv").to_csv(RES_PRESENT / "dash_kpi.csv", index=False)
print("monthly", len(monthly), "products", len(prod), "countries", len(ctry))
