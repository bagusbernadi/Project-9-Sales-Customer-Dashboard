"""Semua path dan konstanta Project 9. ROOT = folder project/."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

RAW_XLSX = ROOT / "data" / "raw" / "online_retail_II.xlsx"
CLEAN_CSV = ROOT / "data" / "clean" / "transactions_clean.csv"
DB_PATH = ROOT / "project_9.duckdb"

SQL_PREP = ROOT / "code" / "1-data-preparation" / "sql"
SQL_ANALYSIS = ROOT / "code" / "2-analysis" / "sql"
RES_PREP = ROOT / "results" / "1-data-preparation"
RES_ANALYSIS = ROOT / "results" / "2-analysis"
RES_PRESENT = ROOT / "results" / "3-presentation"
DOCS_DIR = ROOT / "docs"

# Aturan yang ditetapkan sebelum analisis (lihat docs/definitions.md)
PRODUCT_CODE_RE = r"^\d{5}[A-Za-z]{0,2}$"   # kode produk standar; selain itu = biaya/adjustment/hadiah
MIN_CUSTOMER_N = 10                         # minimal pelanggan per segmen agar ditampilkan
SEGMENT_CUTS = {"VIP": 0.90, "Loyal": 0.70, "Regular": 0.40}  # persentil revenue, sisanya Light

for d in (CLEAN_CSV.parent, RES_PREP, RES_ANALYSIS, RES_PRESENT):
    d.mkdir(parents=True, exist_ok=True)
