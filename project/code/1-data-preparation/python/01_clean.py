"""01 - Gabung dua sheet Online Retail II, bersihkan, dan catat setiap koreksi.

Input : project/data/raw/online_retail_II.xlsx (dua sheet, tidak di-commit)
Output: project/data/clean/transactions_clean.csv (tidak di-commit)
        project/results/1-data-preparation/01_cleaning_log.csv   (jumlah baris per aturan)
        project/results/1-data-preparation/01_dropped_rows.csv   (satu baris per baris yang dibuang)
        project/results/1-data-preparation/01_profile.csv        (profil mentah per sheet)
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common import CLEAN_CSV, PRODUCT_CODE_RE, RAW_XLSX, RES_PREP  # noqa: E402

KEY = ["Invoice", "StockCode", "Description", "Quantity", "InvoiceDate", "Price", "Customer ID", "Country"]
SHEETS = ["Year 2009-2010", "Year 2010-2011"]

xl = pd.ExcelFile(RAW_XLSX)
parts = []
for s in SHEETS:
    d = xl.parse(s)
    d["source_sheet"] = s
    d["raw_row"] = range(2, len(d) + 2)  # nomor baris di sheet (header = baris 1)
    parts.append(d)
raw = pd.concat(parts, ignore_index=True)
n_raw = len(raw)

# --- profil mentah per sheet
prof = []
for s, d in zip(SHEETS, parts):
    for c in KEY:
        prof.append({"sheet": s, "kolom": c, "baris": len(d), "kosong": int(d[c].isna().sum()),
                     "unik": int(d[c].nunique())})
pd.DataFrame(prof).to_csv(RES_PREP / "01_profile.csv", index=False)

log, dropped = [], []
# kolom log: revenue = nilai yang dibuang (status 'dibuang') atau yang terdampak (status 'dicatat')


def drop(mask, rule, note=""):
    """Buang baris yang cocok dengan mask; catat jumlah dan revenue yang terbuang."""
    global raw
    sub = raw[mask]
    rev = float((sub["Quantity"] * sub["Price"]).sum())
    log.append({"langkah": rule, "status": "dibuang", "baris": int(len(sub)), "revenue": round(rev, 2), "catatan": note})
    for r in sub.itertuples():
        dropped.append({"sheet": r.source_sheet, "baris_sumber": r.raw_row, "aturan": rule,
                        "invoice": r.Invoice, "stock_code": r.StockCode, "quantity": r.Quantity,
                        "price": r.Price})
    raw = raw[~mask]


log.append({"langkah": "baris mentah (dua sheet)", "status": "total", "baris": n_raw, "revenue": 0.0, "catatan": ""})

# 1. Duplikat persis (semua 8 kolom). Yang pertama dipertahankan.
dup_mask = raw.duplicated(subset=KEY, keep="first")
kept = raw[~dup_mask][KEY + ["source_sheet"]].drop_duplicates(KEY)
dd = raw[dup_mask][KEY + ["source_sheet"]].merge(kept, on=KEY, how="inner", suffixes=("", "_kept"))
n_cross = int((dd["source_sheet"] != dd["source_sheet_kept"]).sum())
drop(dup_mask, "duplikat persis (8 kolom)",
     f"dari sheet lain (periode overlap Dec 2010): {n_cross}; sisanya duplikat dalam sheet yang sama")

# 2. Harga nol atau negatif (tidak bisa dihitung sebagai revenue)
drop(raw["Price"] <= 0, "harga nol atau negatif", "tidak bisa dipakai untuk revenue")

# 3. Tipe data dan kolom turunan
raw["invoice_no"] = raw["Invoice"].astype(str).str.strip()
raw["is_cancel"] = raw["invoice_no"].str.startswith("C")
raw["is_product"] = raw["StockCode"].astype(str).str.strip().str.match(PRODUCT_CODE_RE)
raw["customer_id"] = raw["Customer ID"].astype("Int64")
raw["invoice_ts"] = pd.to_datetime(raw["InvoiceDate"])
raw["stock_code"] = raw["StockCode"].astype(str).str.strip()
raw["description"] = raw["Description"].astype(str).str.strip().replace({"nan": ""})
raw["country"] = raw["Country"].astype(str).str.strip()
raw["unit_price"] = raw["Price"].astype(float)
raw["quantity"] = raw["Quantity"].astype(int)
raw["line_revenue"] = (raw["quantity"] * raw["unit_price"]).round(2)

# 4. Catatan (tidak dibuang): baris batal, tanpa Customer ID, kode non-produk
notes = [
    ("baris batal (invoice diawali C)", raw["is_cancel"], "tetap dihitung, mengurangi revenue bersih"),
    ("baris tanpa Customer ID", raw["customer_id"].isna(), "tetap dihitung di revenue, tidak dipakai analisis pelanggan"),
    ("kode non-produk (biaya, ongkir, adjustment)", ~raw["is_product"], "tetap dihitung di revenue, tidak dipakai analisis produk"),
    ("baris tanpa deskripsi", raw["description"] == "", "tetap dipakai, deskripsi dibiarkan kosong"),
]
for name, m, note in notes:
    log.append({"langkah": name, "status": "dicatat", "baris": int(m.sum()),
                "revenue": round(float(raw.loc[m, "line_revenue"].sum()), 2), "catatan": note})

out_cols = ["invoice_no", "invoice_ts", "stock_code", "description", "quantity", "unit_price",
            "line_revenue", "customer_id", "country", "is_cancel", "is_product", "source_sheet", "raw_row"]
clean = raw[out_cols].sort_values(["invoice_ts", "invoice_no", "stock_code"]).reset_index(drop=True)
CLEAN_CSV.parent.mkdir(parents=True, exist_ok=True)
clean.to_csv(CLEAN_CSV, index=False)

log.append({"langkah": "baris bersih (dimuat ke database)", "status": "total", "baris": int(len(clean)),
            "revenue": round(float(clean["line_revenue"].sum()), 2), "catatan": "net revenue setelah cleaning"})
pd.DataFrame(log).to_csv(RES_PREP / "01_cleaning_log.csv", index=False)
pd.DataFrame(dropped).to_csv(RES_PREP / "01_dropped_rows.csv", index=False)
print("raw", n_raw, "clean", len(clean), "dropped", len(dropped))
