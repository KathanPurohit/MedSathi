import base64
import logging
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from generic_matcher.jan_aushadhi_price_matcher import match_generic_salt_prices
from utilities.medication_ics_calendar_builder import build_medication_ics_content
from utilities.privacy_pii_redactor import auto_redact_pii_from_image
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


class VoiceGenerateRequest(BaseModel):
    voice_script: str
    language: str = "English"
    voice_gender: str = "female"


@app.post("/api/analyze-document")
async def analyze_medical_document(
    file: UploadFile = File(...),
    language: str = Form("English"),
    voice_gender: str = Form("female"),
):
    """Single endpoint that orchestrates Offline PII Redaction, Vision OCR, Generic Salt Matching, TTS Audio, and Calendar Alarms."""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Please upload a valid image file (JPEG, PNG, WEBP).")

    raw_image_bytes = await file.read()

    # 1. Automatically blackout all patient names, IDs, phone numbers, and QR codes before AI processing
    sanitized_image_bytes = await auto_redact_pii_from_image(raw_image_bytes)

    # 2. Extract structured report & translated summaries from the sanitized image
    try:
        report = extract_prescription_or_report_from_image(
            image_bytes=sanitized_image_bytes,
            mime_type="image/jpeg",
            language=language,
        )
    except Exception as exc:
        err_msg = str(exc)
        logging.error(f"Error during AI document analysis: {err_msg}")
        if "503" in err_msg or "high demand" in err_msg.lower() or "UNAVAILABLE" in err_msg:
            raise HTTPException(
                status_code=503,
                detail="Google AI is currently experiencing high demand. Automatic retries attempted. Please tap Analyze again.",
            )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze medical document: {err_msg}",
        )

    # 3. Match extracted chemical salts against Jan Aushadhi generic pricing
    generic_savings, total_monthly_saved = match_generic_salt_prices(report.medicines)
    report.generic_savings = generic_savings
    report.total_monthly_savings_inr = total_monthly_saved

    # 4. Generate grandparent-friendly MP3 audio voice note in Base64 (supporting female/male doctor voices)
    audio_data_url = await generate_voice_note_base64(
        voice_script=report.voice_script_translated,
        language=language,
        gender=voice_gender,
    )

    # 5. Build 1-tap phone calendar alarm (.ics) content
    ics_calendar_text = build_medication_ics_content(report.medicines)

    # 6. Encode the actual privacy-scrubbed image proof for user verification in the frontend
    encoded_img = base64.b64encode(sanitized_image_bytes).decode("utf-8")
    redacted_image_data_url = f"data:image/jpeg;base64,{encoded_img}"

    return {
        "redacted_image_data_url": redacted_image_data_url,
        "report": report,
        "audio_data_url": audio_data_url,
        "ics_calendar_text": ics_calendar_text,
    }


@app.post("/api/generate-voice")
async def generate_voice_endpoint(request: VoiceGenerateRequest):
    """Allows instant voice toggle (Female Dr. Neerja vs Male Dr. Prabhat) without re-analyzing the image."""
    if not request.voice_script or not request.voice_script.strip():
        raise HTTPException(status_code=400, detail="Voice script cannot be empty.")

    audio_data_url = await generate_voice_note_base64(
        voice_script=request.voice_script,
        language=request.language,
        gender=request.voice_gender,
    )
    return {"audio_data_url": audio_data_url}
