import json
import time
from google import genai
from google.genai import types
from google.genai.errors import ServerError, ClientError
from config.settings import settings
from schemas.prescription_response_schema import SimplifiedPrescriptionReport

CANDIDATE_MODELS = ["gemini-3.5-flash-lite", "gemini-2.5-flash"]


def _call_gemini_with_resilience(
    client: genai.Client,
    contents: list,
    config: types.GenerateContentConfig,
    max_retries_per_model: int = 2,
):
    """Executes Gemini generation with automatic retry and model failover."""
    last_exception = None

    for model_name in CANDIDATE_MODELS:
        for attempt in range(max_retries_per_model):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=config,
                )
                if response and response.text:
                    return response
            except ServerError as exc:
                last_exception = exc
                time.sleep((attempt + 1) * 1.5)
            except ClientError as exc:
                last_exception = exc
                if "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc):
                    time.sleep((attempt + 1) * 2)
                else:
                    raise exc

    if last_exception:
        raise last_exception
    raise RuntimeError("Failed to obtain response from Gemini models.")


def extract_prescription_or_report_from_image(
    image_bytes: bytes, mime_type: str, language: str
) -> SimplifiedPrescriptionReport:
    """Extracts structured medicine schedules, lab findings, and translated scripts using gemini-3.5-flash-lite."""
    gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)

    system_prompt = f"""
    You are an expert Indian clinical pharmacist, medical translator, and diagnostic lab simplifier.
    Analyze the uploaded prescription or lab report image and return a strict JSON response.

    Rules:
    1. TARGET LANGUAGE: Write 'patient_summary_translated', 'voice_script_translated', 'simple_purpose',
       'food_or_drug_clash_warning', 'lab_abnormalities_summary', and 'doctor_questions' strictly in {language}.
    2. SHORTHAND DECODING:
       - '1-0-1' or 'BD' = morning_dose: true, afternoon_dose: false, night_dose: true.
       - '1-1-1' or 'TDS' = all three true.
       - '1-0-0' or 'OD' = morning_dose: true.
       - '0-0-1' or 'HS' = night_dose: true.
       - 'AC' or 'BBF' = 'Before Food'. 'PC' = 'After Food'.
    3. CHEMICAL SALT: Always convert Indian brand names (e.g., Pan-D, Telma 40, Augmentin 625, Glycomet-GP2, Dolo 650)
       into their exact generic chemical salt name in English for catalog price matching.
    4. HOUSEHOLD WARNINGS: Flag real Indian dietary clashes (e.g., avoid taking Iron/Calcium/Thyroid tablets with morning Chai or Milk;
       warn if two prescribed brands share the same salt like Paracetamol).
    5. VOICE SCRIPT: Make 'voice_script_translated' sound like a caring family member speaking directly to an elder in {language},
       under 45 words, clearly explaining the main findings or when to take medicines.
    6. LAB REPORTS (Diagnostic & Blood Tests):
       - If the document is a lab or diagnostic report (e.g. CBC, HbA1c, Lipid Profile, Thyroid TSH, Liver/Kidney tests),
         identify all abnormal or out-of-range values.
       - In 'lab_abnormalities_summary', list each out-of-range test with the patient's value, the reference range, and a simple explanation of what it means in {language}.
       - In 'doctor_questions', formulate 3 clear, practical questions the patient/family should ask the doctor about these test results.
       - If no medications are prescribed on the lab report, return an empty list [] for 'medicines'.
    7. ZERO-PII PRIVACY POLICY:
       - Never include or output the patient's name, age, gender, phone number, address, hospital name, or any personal identifying information in 'patient_summary_translated' or 'voice_script_translated'.
       - Under NO circumstances greet the patient by name (e.g. NEVER say "Hello Lyubochka" or use any person's name).
       - Always address the patient warmly and neutrally (e.g. "Hello! Here is your health summary...", or in Gujarati: "નમસ્તે, તમારો રિપોર્ટ તૈયાર છે...", or in Hindi: "नमस्ते, आपकी रिपोर्ट तैयार है...").

    Respond STRICTLY with a valid JSON object matching this structure:
    {{
      "patient_summary_translated": "Warm, plain-language summary in {language}",
      "voice_script_translated": "Under 45 words caring script in {language}",
      "lab_abnormalities_summary": ["Test name: result vs reference range - simple explanation in {language}"],
      "doctor_questions": ["Question 1 in {language}", "Question 2 in {language}", "Question 3 in {language}"],
      "medicines": [
        {{
          "brand_name": "Prescribed Brand",
          "active_chemical_salt": "Chemical salt in English",
          "dosage_strength": "e.g. 500mg",
          "morning_dose": true,
          "afternoon_dose": false,
          "night_dose": true,
          "meal_instruction": "After Food",
          "duration_days": 5,
          "estimated_branded_strip_inr": 80.0,
          "estimated_generic_strip_inr": 15.0,
          "simple_purpose": "Purpose in {language}",
          "food_or_drug_clash_warning": null
        }}
      ]
    }}
    """

    response = _call_gemini_with_resilience(
        client=gemini_client,
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            system_prompt,
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.1,
        ),
    )

    clean_text = response.text.strip()
    if clean_text.startswith("```json"):
        clean_text = clean_text[7:]
    if clean_text.startswith("```"):
        clean_text = clean_text[3:]
    if clean_text.endswith("```"):
        clean_text = clean_text[:-3]
    clean_text = clean_text.strip()

    return SimplifiedPrescriptionReport.model_validate_json(clean_text)
