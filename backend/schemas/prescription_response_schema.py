from typing import List, Optional
from pydantic import BaseModel, Field


class ExtractedMedicine(BaseModel):
    """Schema for a single medicine extracted from a prescription image."""
    brand_name: str = Field(description="Prescribed brand name on the document")
    active_chemical_salt: str = Field(description="Exact generic chemical salt and composition")
    dosage_strength: str = Field(description="Strength per tablet/dose, e.g., 40mg or 500mg")
    morning_dose: bool = Field(description="True if taken in the morning")
    afternoon_dose: bool = Field(description="True if taken in the afternoon")
    night_dose: bool = Field(description="True if taken at night")
    meal_instruction: str = Field(description="Before Food, After Food, or With Food")
    duration_days: int = Field(default=5, description="Number of days prescribed")
    estimated_branded_strip_inr: float = Field(description="Estimated Indian retail MRP for 1 strip of 10 tablets")
    estimated_generic_strip_inr: float = Field(description="Estimated Jan Aushadhi generic MRP for 1 strip")
    simple_purpose: str = Field(description="1-line plain-language purpose in the requested language")
    food_or_drug_clash_warning: Optional[str] = Field(
        default=None,
        description="Practical household food or duplicate salt warning in the requested language"
    )


class GenericMatchResult(BaseModel):
    """Schema for comparing branded medicine cost against Jan Aushadhi generic pricing."""
    prescribed_brand: str
    generic_salt_name: str
    branded_strip_price_inr: float
    jan_aushadhi_strip_price_inr: float
    monthly_savings_inr: float
    match_source: str = Field(description="'Verified PMBJP Catalog' or 'AI Salt Estimate'")


class SimplifiedPrescriptionReport(BaseModel):
    """Complete structured medical output returned by the Vision AI extractor."""
    patient_summary_translated: str = Field(description="Warm, plain-language summary in the target language")
    voice_script_translated: str = Field(description="20-second grandparent-friendly spoken audio script in target language")
    lab_abnormalities_summary: List[str] = Field(default_factory=list, description="Out-of-range lab values explained simply")
    doctor_questions: List[str] = Field(default_factory=list, description="3 practical questions to ask the doctor")
    medicines: List[ExtractedMedicine] = Field(default_factory=list)
    generic_savings: List[GenericMatchResult] = Field(default_factory=list)
    total_monthly_savings_inr: float = 0.0
