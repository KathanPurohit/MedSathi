import base64
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from generic_matcher.jan_aushadhi_price_matcher import match_generic_salt_prices
from utilities.medication_ics_calendar_builder import build_medication_ics_content
from utilities.voice_note_generator import generate_voice_note_base64
from vision_ai.prescription_vision_extractor import extract_prescription_or_report_from_image

app = FastAPI(title="MedSaathi API - Medical & Prescription Simplifier")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/analyze-document")
async def analyze_medical_document(
    file: UploadFile = File(...),
    language: str = Form("English"),
):
    """Single endpoint that orchestrates Vision OCR, Generic Salt Matching, TTS Audio, and Calendar Alarms."""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Please upload a valid image file (JPEG, PNG, WEBP).")

    image_bytes = await file.read()

    # 1. Extract structured report & translated summaries from image
    report = extract_prescription_or_report_from_image(
        image_bytes=image_bytes,
        mime_type=file.content_type,
        language=language,
    )

    # 2. Match extracted chemical salts against Jan Aushadhi generic pricing
    generic_savings, total_monthly_saved = match_generic_salt_prices(report.medicines)
    report.generic_savings = generic_savings
    report.total_monthly_savings_inr = total_monthly_saved

    # 3. Generate grandparent-friendly MP3 audio voice note in Base64
    audio_data_url = generate_voice_note_base64(
        voice_script=report.voice_script_translated,
        language=language,
    )

    # 4. Build 1-tap phone calendar alarm (.ics) content
    ics_calendar_text = build_medication_ics_content(report.medicines)

    encoded_img = base64.b64encode(image_bytes).decode("utf-8")
    redacted_image_data_url = f"data:{file.content_type};base64,{encoded_img}"

    return {
        "redacted_image_data_url": redacted_image_data_url,
        "report": report,
        "audio_data_url": audio_data_url,
        "ics_calendar_text": ics_calendar_text,
    }
