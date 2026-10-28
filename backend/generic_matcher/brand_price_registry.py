"""Verified retail market pricing for 246,000+ Indian commercial medicines.
Powered by the cleaned A-Z Medicines Dataset of India with indexed SQLite.
"""
import csv
import os
import re
import sqlite3
from typing import Optional, TypedDict

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "indian_medicines.db")
CSV_PATH = os.path.join(BASE_DIR, "A_Z_medicines_dataset_of_India.csv")


class BrandPriceInfo(TypedDict):
    brand_name: str
    actual_mrp: float
    manufacturer: str
    pack_size: str
    active_salt: str


# Common flagship brands with verified pharmacy retail prices (Tata 1mg / Apollo Pharmacy)
TOP_FLAGSHIP_BRANDS: dict[str, BrandPriceInfo] = {
    "shelcal 500": {"brand_name": "Shelcal 500 Tablet", "actual_mrp": 148.20, "manufacturer": "Torrent Pharmaceuticals Ltd", "pack_size": "strip of 15 tablets", "active_salt": "Calcium (500mg) + Vitamin D3 (250IU)"},
    "shelcal hd": {"brand_name": "Shelcal-HD Tablet", "actual_mrp": 165.00, "manufacturer": "Torrent Pharmaceuticals Ltd", "pack_size": "strip of 15 tablets", "active_salt": "Calcium (500mg) + Vitamin D3 (500IU)"},
    "pan d": {"brand_name": "Pan-D Capsule PR", "actual_mrp": 199.00, "manufacturer": "Alkem Laboratories Ltd", "pack_size": "strip of 15 capsule pr", "active_salt": "Pantoprazole (40mg) + Domperidone (30mg)"},
    "pan 40": {"brand_name": "Pan 40 Tablet", "actual_mrp": 155.00, "manufacturer": "Alkem Laboratories Ltd", "pack_size": "strip of 15 tablets", "active_salt": "Pantoprazole (40mg)"},
    "telma 40": {"brand_name": "Telma 40 Tablet", "actual_mrp": 245.95, "manufacturer": "Glenmark Pharmaceuticals Ltd", "pack_size": "strip of 30 tablets", "active_salt": "Telmisartan (40mg)"},
    "telma 20": {"brand_name": "Telma 20 Tablet", "actual_mrp": 125.00, "manufacturer": "Glenmark Pharmaceuticals Ltd", "pack_size": "strip of 15 tablets", "active_salt": "Telmisartan (20mg)"},
    "telma h": {"brand_name": "Telma-H Tablet", "actual_mrp": 280.00, "manufacturer": "Glenmark Pharmaceuticals Ltd", "pack_size": "strip of 15 tablets", "active_salt": "Telmisartan (40mg) + Hydrochlorothiazide (12.5mg)"},
    "telma am": {"brand_name": "Telma-AM Tablet", "actual_mrp": 240.00, "manufacturer": "Glenmark Pharmaceuticals Ltd", "pack_size": "strip of 15 tablets", "active_salt": "Telmisartan (40mg) + Amlodipine (5mg)"},
    "augmentin 625 duo": {"brand_name": "Augmentin 625 Duo Tablet", "actual_mrp": 223.42, "manufacturer": "Glaxo SmithKline Pharmaceuticals Ltd", "pack_size": "strip of 10 tablets", "active_salt": "Amoxycillin (500mg) + Clavulanic Acid (125mg)"},
    "augmentin 625": {"brand_name": "Augmentin 625 Duo Tablet", "actual_mrp": 223.42, "manufacturer": "Glaxo SmithKline Pharmaceuticals Ltd", "pack_size": "strip of 10 tablets", "active_salt": "Amoxycillin (500mg) + Clavulanic Acid (125mg)"},
    "dolo 650": {"brand_name": "Dolo 650 Tablet", "actual_mrp": 34.27, "manufacturer": "Micro Labs Ltd", "pack_size": "strip of 15 tablets", "active_salt": "Paracetamol (650mg)"},
    "calpol 650": {"brand_name": "Calpol 650 Tablet", "actual_mrp": 32.50, "manufacturer": "Glaxo SmithKline Pharmaceuticals Ltd", "pack_size": "strip of 15 tablets", "active_salt": "Paracetamol (650mg)"},
    "glycomet gp 2": {"brand_name": "Glycomet-GP 2 Tablet PR", "actual_mrp": 170.75, "manufacturer": "USV Ltd", "pack_size": "strip of 15 Tablet pr", "active_salt": "Glimepiride (2mg) + Metformin (500mg)"},
    "glycomet gp 1": {"brand_name": "Glycomet-GP 1 Tablet PR", "actual_mrp": 145.00, "manufacturer": "USV Ltd", "pack_size": "strip of 15 Tablet pr", "active_salt": "Glimepiride (1mg) + Metformin (500mg)"},
    "atorva 20": {"brand_name": "Atorva 20 Tablet", "actual_mrp": 247.78, "manufacturer": "Zydus Cadila", "pack_size": "strip of 15 tablets", "active_salt": "Atorvastatin (20mg)"},
    "atorva 10": {"brand_name": "Atorva 10 Tablet", "actual_mrp": 145.00, "manufacturer": "Zydus Cadila", "pack_size": "strip of 15 tablets", "active_salt": "Atorvastatin (10mg)"},
    "montair lc": {"brand_name": "Montair-LC Tablet", "actual_mrp": 336.00, "manufacturer": "Cipla Ltd", "pack_size": "strip of 15 tablets", "active_salt": "Montelukast (10mg) + Levocetirizine (5mg)"},
    "zerodol sp": {"brand_name": "Zerodol-SP Tablet", "actual_mrp": 118.30, "manufacturer": "Ipca Laboratories Ltd", "pack_size": "strip of 10 tablets", "active_salt": "Aceclofenac (100mg) + Paracetamol (325mg) + Serratiopeptidase (15mg)"},
    "zerodol p": {"brand_name": "Zerodol-P Tablet", "actual_mrp": 68.00, "manufacturer": "Ipca Laboratories Ltd", "pack_size": "strip of 10 tablets", "active_salt": "Aceclofenac (100mg) + Paracetamol (325mg)"},
    "azithral 500": {"brand_name": "Azithral 500 Tablet", "actual_mrp": 132.36, "manufacturer": "Alembic Pharmaceuticals Ltd", "pack_size": "strip of 5 tablets", "active_salt": "Azithromycin (500mg)"},
    "thyronorm 50": {"brand_name": "Thyronorm 50mcg Tablet", "actual_mrp": 160.00, "manufacturer": "Abbott India Ltd", "pack_size": "bottle of 120 tablets", "active_salt": "Thyroxine Sodium (50mcg)"},
    "thyronorm 100": {"brand_name": "Thyronorm 100mcg Tablet", "actual_mrp": 195.00, "manufacturer": "Abbott India Ltd", "pack_size": "bottle of 120 tablets", "active_salt": "Thyroxine Sodium (100mcg)"},
    "volini": {"brand_name": "Volini Pain Relief Gel", "actual_mrp": 95.00, "manufacturer": "Sun Pharmaceutical Industries Ltd", "pack_size": "tube of 30 gm", "active_salt": "Diclofenac Diethylamine + Linseed Oil + Methyl Salicylate Gel"},
    "volini gel": {"brand_name": "Volini Pain Relief Gel", "actual_mrp": 95.00, "manufacturer": "Sun Pharmaceutical Industries Ltd", "pack_size": "tube of 30 gm", "active_salt": "Diclofenac Diethylamine + Linseed Oil + Methyl Salicylate Gel"},
}


_DB_CONN: Optional[sqlite3.Connection] = None


def clean_brand_name(brand: str) -> str:
    """Strips dosage forms (Tab., Cap., Syp.) and punctuation for matching."""
    b = brand.lower().strip()
    b = re.sub(r"^(?:tab|capsule|cap|syp|syrup|inj|injection|gel|cream|drops|ointment)[\.\s]+", "", b)
    b = re.sub(r"[^a-z0-9\s]", " ", b)
    return " ".join(b.split())


def _init_db_if_needed():
    """Initializes the SQLite database from the cleaned CSV if not yet built."""
    if os.path.exists(DB_PATH) and os.path.getsize(DB_PATH) > 1024 * 1024:
        return

    if not os.path.exists(CSV_PATH):
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS medicines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand_name TEXT,
            clean_name TEXT,
            price_inr REAL,
            manufacturer TEXT,
            pack_size TEXT,
            composition TEXT,
            clean_salt TEXT
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_clean_name ON medicines (clean_name)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_clean_salt ON medicines (clean_salt)")

    rows_to_insert = []
    with open(CSV_PATH, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for r in reader:
            b_name = r.get("brand_name", "").strip()
            if not b_name:
                continue
            try:
                price = float(r.get("price_inr", 0))
                if price <= 0:
                    continue
            except Exception:
                continue

            mfg = r.get("manufacturer", "").strip()
            pack = r.get("pack_size", "").strip()
            comp = r.get("composition", "").strip()
            c_name = clean_brand_name(b_name)
            c_salt = clean_brand_name(comp)
            rows_to_insert.append((b_name, c_name, price, mfg, pack, comp, c_salt))

    cur.executemany("""
        INSERT INTO medicines (brand_name, clean_name, price_inr, manufacturer, pack_size, composition, clean_salt)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, rows_to_insert)
    conn.commit()
    conn.close()


def _get_db() -> sqlite3.Connection:
    global _DB_CONN
    if _DB_CONN is None:
        _init_db_if_needed()
        _DB_CONN = sqlite3.connect(DB_PATH, check_same_thread=False)
    return _DB_CONN


def get_verified_brand_price(brand_name: str) -> Optional[BrandPriceInfo]:
    """Looks up any prescribed Indian brand name across 246,000+ commercial medicines."""
    if not brand_name:
        return None

    clean = clean_brand_name(brand_name)
    if not clean:
        return None

    # 1. Quick lookup against verified flagship brands
    if clean in TOP_FLAGSHIP_BRANDS:
        return TOP_FLAGSHIP_BRANDS[clean]
    for key, info in TOP_FLAGSHIP_BRANDS.items():
        if key in clean or clean in key:
            return info

    # 2. Database lookup across 246,000+ commercial medicines
    try:
        conn = _get_db()
        cur = conn.cursor()

        # Exact match
        cur.execute(
            "SELECT brand_name, price_inr, manufacturer, pack_size, composition FROM medicines WHERE clean_name = ? LIMIT 1",
            (clean,),
        )
        row = cur.fetchone()

        # Prefix match (e.g. 'telma 40' -> 'telma 40 tablet')
        if not row:
            cur.execute(
                "SELECT brand_name, price_inr, manufacturer, pack_size, composition FROM medicines WHERE clean_name LIKE ? ORDER BY LENGTH(clean_name) ASC LIMIT 1",
                (f"{clean}%",),
            )
            row = cur.fetchone()

        # Substring match (min 4 characters)
        if not row and len(clean) >= 4:
            cur.execute(
                "SELECT brand_name, price_inr, manufacturer, pack_size, composition FROM medicines WHERE clean_name LIKE ? ORDER BY LENGTH(clean_name) ASC LIMIT 1",
                (f"%{clean}%",),
            )
            row = cur.fetchone()

        if row:
            return {
                "brand_name": row[0],
                "actual_mrp": float(row[1]),
                "manufacturer": row[2] or "Generic/Commercial",
                "pack_size": row[3] or "strip",
                "active_salt": row[4] or "",
            }
    except Exception:
        pass

    return None


def get_commercial_brand_for_salt(salt_name: str) -> Optional[BrandPriceInfo]:
    """Finds a prominent commercial brand equivalent for a generic salt composition."""
    if not salt_name:
        return None

    clean_s = clean_brand_name(salt_name)
    tokens = [t for t in clean_s.split() if len(t) >= 4 and t not in ("tablets", "capsules", "syrup", "drops", "acid", "sodium")]
    if not tokens:
        return None

    try:
        conn = _get_db()
        cur = conn.cursor()
        like_query = "%" + "%".join(tokens[:2]) + "%"
        cur.execute(
            "SELECT brand_name, price_inr, manufacturer, pack_size, composition FROM medicines WHERE clean_salt LIKE ? ORDER BY LENGTH(clean_name) ASC LIMIT 1",
            (like_query,),
        )
        row = cur.fetchone()
        if row:
            return {
                "brand_name": row[0],
                "actual_mrp": float(row[1]),
                "manufacturer": row[2] or "Commercial Pharmacy",
                "pack_size": row[3] or "strip",
                "active_salt": row[4] or "",
            }
    except Exception:
        pass

    return None
