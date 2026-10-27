"""07 - Cek silang dashboard vs SQL (Q13). Menjalankan app.py dengan Streamlit AppTest dan membandingkan
angka yang tampil di dashboard dengan hasil query SQL di project/results/2-analysis/.

Output: project/results/3-presentation/07_dashboard_check.csv
"""
import sys
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common import RES_ANALYSIS, RES_PRESENT  # noqa: E402

APP = Path(__file__).resolve().parents[1] / "streamlit" / "app.py"
at = AppTest.from_file(str(APP), default_timeout=120).run()
assert not at.exception, at.exception

metrics = {m.label: m.value for m in at.metric}


def metric(prefix):
    return next(v for k, v in metrics.items() if k.startswith(prefix))
kpi = pd.read_csv(RES_ANALYSIS / "03_kpi.csv").iloc[0]
prod = pd.read_csv(RES_ANALYSIS / "q4_product_revenue.csv")
seg_sql = pd.read_csv(RES_ANALYSIS / "q7_segments.csv").set_index("segment")
seg_dash = pd.read_csv(RES_PRESENT / "dash_segments.csv").set_index("segment")


def money(v):
    return float(str(v).replace("£", "").replace(",", ""))


rev_dash = money(metric("Net revenue"))
ord_dash = float(str(metric("Invoice non-batal")).replace(",", ""))
rows = [
    {"cek": "net revenue (dashboard vs SQL)", "dashboard": rev_dash, "sql": round(kpi["net_revenue"], 0),
     "selisih": round(abs(rev_dash - round(kpi["net_revenue"], 0)), 2)},
    {"cek": "invoice non-batal (dashboard vs SQL)", "dashboard": ord_dash, "sql": float(kpi["orders"]),
     "selisih": abs(ord_dash - float(kpi["orders"]))},
    {"cek": "jumlah pelanggan per segmen (total)", "dashboard": float(seg_dash["pelanggan"].sum()),
     "sql": float(seg_sql["pelanggan"].sum()),
     "selisih": abs(float(seg_dash["pelanggan"].sum()) - float(seg_sql["pelanggan"].sum()))},
    {"cek": "revenue produk teratas (dashboard vs SQL)", "dashboard": float(pd.read_csv(RES_PRESENT / "dash_products.csv")["net_revenue"].iloc[0]),
     "sql": float(prod["net_revenue"].iloc[0]),
     "selisih": abs(float(pd.read_csv(RES_PRESENT / "dash_products.csv")["net_revenue"].iloc[0]) - float(prod["net_revenue"].iloc[0]))},
]
out = pd.DataFrame(rows)
out["status"] = ["PASS" if abs(s) < 0.5 else "FAIL" for s in out["selisih"]]
out.to_csv(RES_PRESENT / "07_dashboard_check.csv", index=False)
print(out.to_string(index=False))
