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


def extract_prescription_or_report_from_images(
    images_bytes: list[bytes], language: str
) -> SimplifiedPrescriptionReport:
    """Extracts structured medicine schedules, lab findings, and translated scripts across single or multi-page documents."""
    gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)

    system_prompt = f"""
    You are an expert Indian clinical pharmacist, medical translator, and diagnostic lab simplifier.
    Analyze the uploaded prescription or lab report (which may contain one or multiple pages) and return a strict JSON response.
    If the document has multiple pages, integrate all medicines and diagnostic tests across all pages into a single comprehensive report.

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
    5. NATURAL, NON-REPETITIVE SPOKEN VOICE SCRIPT:
       - 'voice_script_translated': This is the EXACT voice note heard by the patient or elder in {language}. It must sound like a warm, caring Indian physician or family caregiver speaking directly to them in fluent, natural conversational speech.
       - STRICT ANTI-REPETITION RULES:
         * NEVER repeat any medicine's name multiple times across the script.
         * For medicines taken multiple times a day (e.g. 1-0-1 or twice daily like Glycomet-GP 2), state the schedule ONCE in natural speech (e.g. "For your sugar, take Glycomet twice a day—with your morning and night meals"). Do NOT mention its name again later in the night section.
         * For as-needed / SOS medicines (like Dolo 650 for pain/fever), clearly state they are ONLY to be taken if there is pain or fever, not as a mandatory daily pill.
         * NEVER read clinical prefixes or package terms aloud (do NOT say "Tablet", "Capsule PR", "Film Coated", "IP", "10's"). Say only the familiar brand name: "Pan-D", "Telma 40", "Shelcal", "Atorva", "Dolo".
       - NATURAL CONVERSATIONAL FLOW (NOT A ROBOTIC CHECKLIST):
         * Connect the instructions smoothly with natural spoken phrasing:
           - Start with an empty stomach reminder (e.g. 30 minutes before breakfast for acidity).
           - Flow into post-breakfast medicines (e.g. for blood pressure).
           - Flow into afternoon medicines with lunch (e.g. calcium).
           - Flow into evening/bedtime medicines with dinner (e.g. cholesterol).
           - Weave important food rules smoothly (e.g. 2-hour gap between calcium and tea/milk, low-salt diet).
         * Avoid robotic checklist transitions like "Morning list: ... Afternoon list: ...". Use warm, flowing conversational sentences.
       - REFERENCE FLOW IN {language}:
         * If {language} is Gujarati: "નમસ્તે! ડૉક્ટરે તમારા માટે આપેલી દવાઓની વિગત આ પ્રમાણે છે. સવારે નાસ્તાના અડધો કલાક પહેલાં ભૂખ્યા પેટે એસિડિટી માટે પેન-ડી લેવાની છે. નાસ્તા પછી બીપી માટે ટેલ્મા-40 લેશો. ડાયાબિટીસ માટે ગ્લાયકોમેટ દિવસમાં બે વાર—સવારે અને રાત્રે જમવાની સાથે લેવાની છે. બપોરે જમ્યા પછી હાડકાં માટે શેલકલ લેશો, પણ ખાસ ધ્યાન રાખજો કે આ ગોળી ચા કે દૂધ સાથે ન લેવાય, વચ્ચે બે કલાકનું અંતર રાખજો. રાત્રે જમ્યા પછી કોલેસ્ટ્રોલ માટે એટોર્વા લેશો. જો શરીર દુખે કે તાવ જેવું લાગે તો જ જરૂર મુજબ ડોલો લેજો. સમયસર દવાઓ લેજો અને સાચવજો!"
         * If {language} is Hindi: "नमस्ते! आपके डॉक्टर द्वारा बताई गई दवाइयों की पूरी जानकारी इस प्रकार है। सुबह नाश्ते से आधा घंटा पहले खाली पेट गैस और एसिडिटी के लिए पैन-ડી लें। नाश्ते के बाद ब्लड प्रेशर के लिए टेल्मा-40 लें। शुगर के लिए ग्लाइकोमेट दिन में दो बार—सुबह और रात के भोजन के साथ लें। दोपहर के खाने के बाद हड्डियों के लिए शेलकल लें, पर ध्यान रखें कि इसे चाय या दूध के साथ न लें, कम से कम दो घंटे का अंतर रखें। रात को खाने के बाद कोलेस्ट्रॉल के लिए एटोर्वा लें। अगर शरीर दर्द या हल्का बुखार हो तो ही डोलो लें। अपना ख्याल रखें और समय पर दवाइयां लें।"
         * If {language} is English: "Hello! Here is your medicine schedule from your doctor. First thing in the morning, 30 minutes before breakfast on an empty stomach, take Pan-D for acidity. After breakfast, take Telma-40 for your blood pressure. For diabetes, take Glycomet twice daily—with your morning and night meals. After lunch, take Shelcal for bone strength, but please keep a 2-hour gap between this and your morning tea or milk. At bedtime after dinner, take Atorva for cholesterol. If you have fever or body aches, take Dolo only as needed. Please take your medicines on time and take care!"
       - 'patient_summary_translated': Provide an equally smooth, comprehensive written paragraph in {language} explaining all medicines, daily routine, and precautions clearly.
    6. LAB REPORTS (Diagnostic & Blood Tests):
       - If the document is a lab or diagnostic report (e.g. CBC, HbA1c, Lipid Profile, Thyroid TSH, Liver/Kidney tests),
         identify all abnormal or out-of-range values across all pages.
       - In 'lab_abnormalities_summary', list each out-of-range test with the patient's value, the reference range, and a simple explanation of what it means in {language}.
       - In 'doctor_questions', formulate 3 clear, practical questions the patient/family should ask the doctor about these test results.
       - If no medications are prescribed on the lab report, return an empty list [] for 'medicines'.
    7. ZERO-PII PRIVACY POLICY:
       - Never include or output the patient's name, age, gender, phone number, address, hospital name, or any personal identifying information in 'patient_summary_translated' or 'voice_script_translated'.
       - Under NO circumstances greet the patient by name (e.g. NEVER say "Hello Lyubochka" or use any person's name).
       - Always address the patient warmly and neutrally (e.g. "Hello! Here is your health summary...", or in Gujarati: "નમસ્તે, તમારો સંપૂર્ણ દવા અને સ્વાસ્થ્ય અહેવાલ તૈયાર છે...", or in Hindi: "नमस्ते, आपकी पूरी दवाइयों और स्वास्थ्य की जानकारी तैयार है...").
    8. ACTUAL PHARMACY BRAND MRP:
       - In 'estimated_branded_strip_inr', provide the REAL, ACCURATE current Indian retail market MRP (as sold on Tata 1mg / Apollo Pharmacy / PharmEasy for a standard strip of 10 or 15 tablets) for the specific prescribed brand name (e.g. Augmentin 625 Duo = ~223 INR, Pan-D = ~199 INR, Telma 40 = ~223 INR, Dolo 650 = ~34 INR, Shelcal 500 = ~148 INR, Glycomet-GP 2 = ~188 INR, Montair-LC = ~182 INR, Atorva 20 = ~285 INR). Do NOT mock or invent rough multipliers.

    Respond STRICTLY with a valid JSON object matching this structure:
    {{
      "patient_summary_translated": "Comprehensive, plain-language written summary in {language} covering all prescribed medicines, purposes, and precautions",
      "voice_script_translated": "Exhaustive, caring, chronological audio speech in {language} covering every medicine by name, morning/afternoon/night schedule, meal rules, and warnings",
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

    contents = [
        types.Part.from_bytes(data=img, mime_type="image/jpeg")
        for img in images_bytes
    ]
    contents.append(system_prompt)

    response = _call_gemini_with_resilience(
        client=gemini_client,
        contents=contents,
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


def extract_prescription_or_report_from_image(
    image_bytes: bytes, mime_type: str, language: str
) -> SimplifiedPrescriptionReport:
    """Backwards-compatible wrapper for single image extraction."""
    return extract_prescription_or_report_from_images([image_bytes], language)
