"""09 - Membuat dan menjalankan notebook analisis (Q1-Q14) dari hasil tahap sebelumnya.

Output: project/results/3-presentation/analysis.ipynb (sudah dieksekusi)
"""
import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common import RES_PRESENT, ROOT  # noqa: E402

nb = nbformat.v4.new_notebook()
md = lambda t: nbformat.v4.new_markdown_cell(t)  # noqa: E731
code = lambda t: nbformat.v4.new_code_cell(t)  # noqa: E731

nb.cells = [
    md("# Sales & Customer Analysis: Online Retail II\n"
       "Notebook ini membaca hasil query SQL dan menampilkan jawaban Q1-Q14. Semua angka berasal dari "
       "`project/results/`. Jalankan `01` sampai `08` lebih dulu jika folder hasil kosong."),
    code("import pandas as pd\nimport matplotlib.pyplot as plt\n"
         "R = '../2-analysis/'  # relatif terhadap results/3-presentation\n"
         "pd.set_option('display.float_format', lambda v: f'{v:,.2f}')"),
    md("## Q1 Tren revenue dan musim\nRevenue naik turun setiap tahun. Rata-rata per bulan dipakai untuk menguji musim."),
    code("m = pd.read_csv(R + 'q1_monthly.csv')\n"
         "plt.figure(figsize=(10, 3)); plt.plot(m['bulan'], m['net_revenue']/1e3, marker='o'); "
         "plt.xticks(rotation=60, fontsize=7); plt.ylabel('ribu GBP'); plt.title('Net revenue bulanan'); plt.show()\n"
         "pd.read_csv(R + 'q1_season.csv')"),
    md("## Q2 Negara di luar Inggris\nNegara lain menyumbang sebagian kecil revenue."),
    code("c = pd.read_csv(R + 'q2_country.csv')\n"
         "c.head(11)"),
    md("## Q4 Pareto produk\nJumlah produk yang mencapai 80% revenue dibandingkan total produk."),
    code("p = pd.read_csv(R + 'q4_pareto_product.csv')\n"
         "n80 = int((p['cum_share'] < 0.8).sum() + 1)\n"
         "print(f'{n80:,} dari {len(p):,} produk mencapai 80% revenue')"),
    md("## Q6-Q8 Pelanggan, segmen, dan repeat purchase"),
    code("pd.read_csv(R + 'q6_top10.csv')\n"),
    code("pd.read_csv(R + 'q7_segments.csv')"),
    code("pd.read_csv(R + 'q8_repeat_segment.csv')"),
    md("## Q10 Skenario retensi (estimated)\nTambahan revenue jika repeat purchase rate naik. Ini estimasi, bukan hasil eksperimen."),
    code("pd.read_csv(R + 'q10_retention_scenarios.csv')"),
    md("## Q12-Q14 Validitas data\nRingkasan pembersihan dan cek silang."),
    code("pd.read_csv('../1-data-preparation/01_cleaning_log.csv')"),
    code("pd.read_csv(R + 'q12_impact.csv')"),
    code("pd.read_csv(R + '04_crosscheck_sql_pandas.csv')"),
    code("pd.read_csv(R + '05_crosscheck_spreadsheet.csv')"),
    md("## Hipotesis\nVerdict mengikuti aturan di `docs/definitions.md`."),
    code("pd.read_csv(R + '03_hypothesis_tests.csv')"),
]

out = RES_PRESENT / "analysis.ipynb"
client = NotebookClient(nb, timeout=600, kernel_name="python3",
                        resources={"metadata": {"path": str((ROOT / "results" / "3-presentation").resolve())}})
client.execute()
nbformat.write(nb, out)
errors = [c for c in nb.cells if c.cell_type == "code" for o in c.get("outputs", []) if o.get("output_type") == "error"]
print("ok", out, "error cells:", len(errors))
