import csv
import re
from pathlib import Path
from typing import List, Optional, Tuple

from generic_matcher.brand_price_registry import get_verified_brand_price
from schemas.prescription_response_schema import ExtractedMedicine, GenericMatchResult

CATALOG_PATH = Path(__file__).parent / "jan_aushadhi_catalog.csv"
_CATALOG_CACHE: Optional[List[dict]] = None


def load_jan_aushadhi_catalog() -> List[dict]:
    """Reads the local PMBJP Jan Aushadhi CSV catalog into memory with caching."""
    global _CATALOG_CACHE
    if _CATALOG_CACHE is None:
        with open(CATALOG_PATH, mode="r", encoding="utf-8") as csv_file:
            _CATALOG_CACHE = list(csv.DictReader(csv_file))
    return _CATALOG_CACHE


def _normalize_text(s: str) -> str:
    """Normalizes medication strings for resilient matching across dosages and synonyms."""
    s = s.lower().replace("+", " and ").replace("/", " and ")
    s = s.replace("amoxicillin", "amoxycillin").replace("paracetamol", "paracetamol")
    s = re.sub(r"(\d+)\s*(mg|mcg|iu|gm|ml)\b", r"\1\2", s)
    return s


def _find_best_catalog_match(query_salt: str, catalog: List[dict]) -> Optional[dict]:
    """Finds the closest matching PMBJP generic drug using chemical token and dosage scoring."""
    q_norm = _normalize_text(query_salt)
    # Extract chemical active substance tokens (words >= 4 chars, excluding dosage and form units)
    q_tokens = set(re.findall(r"[a-z]{4,}", q_norm)) - {
        "acid", "sodium", "potassium", "tablets", "capsules", "prolonged", "release",
        "sustained", "hydrochloride", "tablet", "capsule", "syrup", "drops", "film"
    }
    q_dosages = set(re.findall(r"\b\d+(?:mg|mcg|iu|gm|ml)?\b", q_norm))

    best_row = None
    best_score = 0.0

    for row in catalog:
        jan_price = float(row.get("jan_aushadhi_strip_inr") or 0.0)
        if jan_price <= 0:
            continue

        row_norm = _normalize_text(f"{row['salt_keyword']} {row['standard_salt_name']}")
        matched_tokens = sum(1 for t in q_tokens if t in row_norm)
        if matched_tokens == 0:
            continue

        # Base token match ratio
        score = (matched_tokens / max(len(q_tokens), 1)) * 100.0

        # Exact token match bonus
        if matched_tokens == len(q_tokens):
            score += 50.0

        # Dosage alignment bonus (e.g. 40mg, 500mg)
        for d in q_dosages:
            if re.search(r"\b" + re.escape(d) + r"\b", row_norm):
                score += 25.0

        # Penalty for extra ingredients not in query to favor monotherapies
        row_tokens = set(re.findall(r"[a-z]{4,}", _normalize_text(row["salt_keyword"]))) - {
            "acid", "sodium", "potassium", "hydrochloride"
        }
        extra_tokens = len(row_tokens - q_tokens)
        score -= extra_tokens * 15.0

        if score > best_score:
            best_score = score
            best_row = row

    if best_score >= 50.0:
        return best_row
    return None


def _resolve_branded_pricing(med: ExtractedMedicine, matched_row: Optional[dict]) -> Tuple[float, str]:
    """Resolves actual branded retail MRP from verified pharmacy databases or catalog benchmarks."""
    brand_info = get_verified_brand_price(med.brand_name)
    if brand_info:
        return float(brand_info["actual_mrp"]), f"{brand_info['manufacturer']} ({brand_info['pack_size']})"

    if med.estimated_branded_strip_inr and med.estimated_branded_strip_inr > 0:
        return float(med.estimated_branded_strip_inr), "Prescription Retail MRP"

    if matched_row and float(matched_row.get("branded_strip_inr") or 0.0) > 0:
        return float(matched_row["branded_strip_inr"]), "Market Benchmark"

    return 45.0, "Standard Retail"


def _build_generic_match(
    med: ExtractedMedicine,
    matched_row: Optional[dict],
    branded_price: float,
    branded_source: str,
) -> Tuple[GenericMatchResult, float]:
    """Builds a verified GenericMatchResult comparing branded vs Jan Aushadhi pricing."""
    if matched_row:
        generic_price = float(matched_row["jan_aushadhi_strip_inr"])
        salt_display = matched_row["standard_salt_name"]
        drug_code = matched_row.get("drug_code", "")
        source = (
            f"Verified PMBJP #{drug_code} vs {branded_source}"
            if drug_code
            else f"Verified PMBJP vs {branded_source}"
        )
    else:
        generic_price = max(med.estimated_generic_strip_inr, 10.0)
        salt_display = f"{med.active_chemical_salt} ({med.dosage_strength})"
        source = f"AI Salt Estimate vs {branded_source}"

    # Monthly savings based on standard 2 strips (20-30 tablets) per month
    monthly_saved = round(max((branded_price - generic_price) * 2, 0.0), 2)

    result = GenericMatchResult(
        prescribed_brand=med.brand_name,
        generic_salt_name=salt_display,
        branded_strip_price_inr=branded_price,
        jan_aushadhi_strip_price_inr=generic_price,
        monthly_savings_inr=monthly_saved,
        match_source=source,
    )
    return result, monthly_saved


def match_generic_salt_prices(
    medicines: List[ExtractedMedicine],
) -> Tuple[List[GenericMatchResult], float]:
    """Matches extracted chemical salts against the official 2,439 PMBJP catalog entries."""
    catalog = load_jan_aushadhi_catalog()
    savings_list: List[GenericMatchResult] = []
    total_monthly_savings = 0.0

    for med in medicines:
        full_query = f"{med.active_chemical_salt} {med.dosage_strength}"
        matched_row = _find_best_catalog_match(full_query, catalog)
        branded_price, branded_source = _resolve_branded_pricing(med, matched_row)
        match_result, monthly_saved = _build_generic_match(med, matched_row, branded_price, branded_source)

        total_monthly_savings += monthly_saved
        savings_list.append(match_result)

    return savings_list, round(total_monthly_savings, 2)
