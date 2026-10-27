/** Strict TypeScript contracts matching the FastAPI Pydantic response schemas. */

export type SupportedLanguage = "English" | "Hindi" | "Gujarati";
export type VoiceGender = "female" | "male";

export interface ExtractedMedicine {
  brand_name: string;
  active_chemical_salt: string;
  dosage_strength: string;
  morning_dose: boolean;
  afternoon_dose: boolean;
  night_dose: boolean;
  meal_instruction: string;
  duration_days: number;
  estimated_branded_strip_inr: number;
  estimated_generic_strip_inr: number;
  simple_purpose: string;
  food_or_drug_clash_warning?: string | null;
}

export interface GenericMatchResult {
  prescribed_brand: string;
  generic_salt_name: string;
  branded_strip_price_inr: number;
  jan_aushadhi_strip_price_inr: number;
  monthly_savings_inr: number;
  match_source: string;
}

export interface SimplifiedPrescriptionReport {
  patient_summary_translated: string;
  voice_script_translated: string;
  lab_abnormalities_summary: string[];
  doctor_questions: string[];
  medicines: ExtractedMedicine[];
  generic_savings: GenericMatchResult[];
  total_monthly_savings_inr: number;
}

export interface AnalyzeDocumentApiResponse {
  redacted_image_data_url: string;
  redacted_pages?: string[];
  total_pages?: number;
  report: SimplifiedPrescriptionReport;
  audio_data_url: string;
  ics_calendar_text: string;
}
