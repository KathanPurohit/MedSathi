import base64
import io
import logging
from typing import Any
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pypdfium2 as pdfium

from generic_matcher.jan_aushadhi_price_matcher import match_generic_salt_prices
from schemas.prescription_response_schema import SimplifiedPrescriptionReport
from utilities.medication_ics_calendar_builder import build_medication_ics_content
from utilities.privacy_pii_redactor import auto_redact_pii_from_image
from utilities.voice_note_generator import generate_voice_note_base64
from vision_ai.prescription_vision_extractor import extract_prescription_or_report_from_images

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


def _validate_and_extract_pages(raw_bytes: bytes, filename: str | None, content_type: str | None) -> list[bytes]:
    """Validates document format and renders single or multi-page documents to high-resolution JPEG bytes."""
    is_pdf = (
        (content_type and "pdf" in content_type.lower())
        or (filename and filename.lower().endswith(".pdf"))
        or raw_bytes.startswith(b"%PDF")
    )
    is_image = (
        (content_type and content_type.startswith("image/"))
        or (filename and any(filename.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp"]))
    )

    if not is_pdf and not is_image:
        raise HTTPException(
            status_code=400,
            detail="Please upload a valid image file (JPEG, PNG, WEBP) or multi-page PDF document.",
        )

    if not is_pdf:
        return [raw_bytes]

    try:
        pdf = pdfium.PdfDocument(raw_bytes)
        print(f"[Document Engine] Detected multi-page PDF with {len(pdf)} page(s).")
        rendered_pages: list[bytes] = []
        for page in pdf:
            pil_page = page.render(scale=2.0).to_pil().convert("RGB")
            buf = io.BytesIO()
            pil_page.save(buf, format="JPEG", quality=92)
            rendered_pages.append(buf.getvalue())
        return rendered_pages
    except Exception as exc:
        logging.error(f"Error parsing PDF document: {exc}")
        raise HTTPException(status_code=400, detail=f"Failed to read PDF document: {exc}")


async def _redact_document_pages(page_images_bytes: list[bytes]) -> list[bytes]:
    """Applies client/offline PII scrubbing across all document pages."""
    sanitized_pages: list[bytes] = []
    for page_bytes in page_images_bytes:
        redacted = await auto_redact_pii_from_image(page_bytes)
        sanitized_pages.append(redacted)
    return sanitized_pages


def _extract_report_with_resilience(sanitized_pages: list[bytes], language: str) -> SimplifiedPrescriptionReport:
    """Delegates multimodal structured extraction to Gemini with domain error translation."""
    try:
        return extract_prescription_or_report_from_images(
            images_bytes=sanitized_pages,
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


def _serialize_analysis_response(
    report: SimplifiedPrescriptionReport,
    sanitized_pages: list[bytes],
    audio_data_url: str,
    ics_calendar_text: str,
) -> dict[str, Any]:
    """Packages the analysis results and redacted image data URLs for client presentation."""
    redacted_pages_urls = [
        f"data:image/jpeg;base64,{base64.b64encode(b).decode('utf-8')}"
        for b in sanitized_pages
    ]
    return {
        "redacted_image_data_url": redacted_pages_urls[0],
        "redacted_pages": redacted_pages_urls,
        "total_pages": len(redacted_pages_urls),
        "report": report,
        "audio_data_url": audio_data_url,
        "ics_calendar_text": ics_calendar_text,
    }


@app.post("/api/analyze-document")
async def analyze_medical_document(
    file: UploadFile = File(...),
    language: str = Form("English"),
    voice_gender: str = Form("female"),
):
    """Orchestrates document rasterization, PII sanitization, multimodal analysis, pricing, and TTS."""
    raw_bytes = await file.read()
    if not raw_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # 1. Render all document pages
    page_images_bytes = _validate_and_extract_pages(raw_bytes, file.filename, file.content_type)

    # 2. Blackout patient demographics and identifiers
    sanitized_pages_bytes = await _redact_document_pages(page_images_bytes)

    # 3. Multimodal vision extraction
    report = _extract_report_with_resilience(sanitized_pages_bytes, language)

    # 4. Generic pricing & savings matching
    generic_savings, total_monthly_saved = match_generic_salt_prices(report.medicines)
    report.generic_savings = generic_savings
    report.total_monthly_savings_inr = total_monthly_saved

    # 5. Audio synthesis
    audio_data_url = await generate_voice_note_base64(
        voice_script=report.voice_script_translated,
        language=language,
        gender=voice_gender,
    )

    # 6. Medication calendar alarms
    ics_calendar_text = build_medication_ics_content(report.medicines)

    # 7. Package and serialize response
    return _serialize_analysis_response(
        report=report,
        sanitized_pages=sanitized_pages_bytes,
        audio_data_url=audio_data_url,
        ics_calendar_text=ics_calendar_text,
    )


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
