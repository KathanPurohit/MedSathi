import csv
from pathlib import Path
from typing import List, Tuple
from schemas.prescription_response_schema import ExtractedMedicine, GenericMatchResult


CATALOG_PATH = Path(__file__).parent / "jan_aushadhi_catalog.csv"


def load_jan_aushadhi_catalog() -> List[dict]:
    """Reads the local PMBJP Jan Aushadhi CSV catalog into memory."""
    with open(CATALOG_PATH, mode="r", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def match_generic_salt_prices(
    medicines: List[ExtractedMedicine],
) -> Tuple[List[GenericMatchResult], float]:
    """Matches extracted chemical salts against the PMBJP catalog with AI fallback pricing."""
    catalog = load_jan_aushadhi_catalog()
    savings_list: List[GenericMatchResult] = []
    total_monthly_savings = 0.0

    for med in medicines:
        salt_lower = med.active_chemical_salt.lower()
        matched_row = next(
            (row for row in catalog if row["salt_keyword"] in salt_lower),
            None,
        )

        if matched_row:
            branded_price = float(matched_row["branded_strip_inr"])
            generic_price = float(matched_row["jan_aushadhi_strip_inr"])
            salt_display = matched_row["standard_salt_name"]
            source = "Verified PMBJP Catalog"
        else:
            branded_price = max(med.estimated_branded_strip_inr, 30.0)
            generic_price = max(med.estimated_generic_strip_inr, 10.0)
            salt_display = f"{med.active_chemical_salt} ({med.dosage_strength})"
            source = "AI Salt Estimate"

        # Calculate monthly savings based on 2 strips (20 tablets) per month
        monthly_saved = round(max((branded_price - generic_price) * 2, 0.0), 2)
        total_monthly_savings += monthly_saved

        savings_list.append(
            GenericMatchResult(
                prescribed_brand=med.brand_name,
                generic_salt_name=salt_display,
                branded_strip_price_inr=branded_price,
                jan_aushadhi_strip_price_inr=generic_price,
                monthly_savings_inr=monthly_saved,
                match_source=source,
            )
        )

    return savings_list, round(total_monthly_savings, 2)
