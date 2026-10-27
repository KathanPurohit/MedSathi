import json
from google import genai
from google.genai import types
from config.settings import settings
from schemas.prescription_response_schema import SimplifiedPrescriptionReport


def extract_prescription_or_report_from_image(
    image_bytes: bytes, mime_type: str, language: str
) -> SimplifiedPrescriptionReport:
    """Extracts structured medicine schedules, lab findings, and translated scripts using Gemini 2.5 Flash."""
    gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
    schema_json = json.dumps(SimplifiedPrescriptionReport.model_json_schema(), indent=2)

    system_prompt = f"""
    You are an expert Indian clinical pharmacist and medical translator.
    Analyze the uploaded prescription or lab report image and return a strict JSON response matching the schema below.

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
       into their exact generic chemical salt name in English so our CSV matcher can look them up.
    4. HOUSEHOLD WARNINGS: Flag real Indian dietary clashes (e.g., avoid taking Iron/Calcium/Thyroid tablets with morning Chai or Milk;
       warn if two prescribed brands share the same salt like Paracetamol).
    5. VOICE SCRIPT: Make 'voice_script_translated' sound like a caring family member speaking directly to an elder in {language},
       under 45 words, clearly stating when to take each medicine.

    Respond STRICTLY with a valid JSON object conforming to this JSON Schema:
    {schema_json}
    """

    response = gemini_client.models.generate_content(
        model="gemini-2.5-flash",
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
