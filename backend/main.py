import base64
import io
import logging
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pypdfium2 as pdfium
from generic_matcher.jan_aushadhi_price_matcher import match_generic_salt_prices
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


@app.post("/api/analyze-document")
async def analyze_medical_document(
    file: UploadFile = File(...),
    language: str = Form("English"),
    voice_gender: str = Form("female"),
):
    """Single endpoint supporting Single & Multi-Page PDFs and Images with Offline PII Redaction, Vision AI, and TTS."""
    raw_bytes = await file.read()
    if not raw_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    is_pdf = (
        (file.content_type and "pdf" in file.content_type.lower())
        or (file.filename and file.filename.lower().endswith(".pdf"))
        or raw_bytes.startswith(b"%PDF")
    )
    is_image = (
        (file.content_type and file.content_type.startswith("image/"))
        or (file.filename and any(file.filename.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp"]))
    )

    if not is_pdf and not is_image:
        raise HTTPException(
            status_code=400,
            detail="Please upload a valid image file (JPEG, PNG, WEBP) or multi-page PDF document.",
        )

    # 1. Render all document pages to high-resolution images
    page_images_bytes: list[bytes] = []
    if is_pdf:
        try:
            pdf = pdfium.PdfDocument(raw_bytes)
            print(f"[Document Engine] Detected multi-page PDF with {len(pdf)} page(s).")
            for page in pdf:
                pil_page = page.render(scale=2.0).to_pil().convert("RGB")
                buf = io.BytesIO()
                pil_page.save(buf, format="JPEG", quality=92)
                page_images_bytes.append(buf.getvalue())
        except Exception as exc:
            logging.error(f"Error parsing PDF document: {exc}")
            raise HTTPException(status_code=400, detail=f"Failed to read PDF document: {exc}")
    else:
        page_images_bytes = [raw_bytes]

    # 2. Automatically blackout all patient demographics, IDs, and QR codes across all pages
    sanitized_pages_bytes: list[bytes] = []
    for idx, page_bytes in enumerate(page_images_bytes, start=1):
        redacted = await auto_redact_pii_from_image(page_bytes)
        sanitized_pages_bytes.append(redacted)

    # 3. Extract unified structured report across all sanitized pages using Gemini Multimodal Vision AI
    try:
        report = extract_prescription_or_report_from_images(
            images_bytes=sanitized_pages_bytes,
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

    # 4. Match extracted chemical salts against Jan Aushadhi generic pricing
    generic_savings, total_monthly_saved = match_generic_salt_prices(report.medicines)
    report.generic_savings = generic_savings
    report.total_monthly_savings_inr = total_monthly_saved

    # 5. Generate grandparent-friendly MP3 audio voice note in Base64 (supporting female/male doctor voices)
    audio_data_url = await generate_voice_note_base64(
        voice_script=report.voice_script_translated,
        language=language,
        gender=voice_gender,
    )

    # 6. Build 1-tap phone calendar alarm (.ics) content
    ics_calendar_text = build_medication_ics_content(report.medicines)

    # 7. Encode the actual privacy-scrubbed image proof for all pages
    redacted_pages_urls = [
        f"data:image/jpeg;base64,{base64.b64encode(b).decode('utf-8')}"
        for b in sanitized_pages_bytes
    ]

    return {
        "redacted_image_data_url": redacted_pages_urls[0],
        "redacted_pages": redacted_pages_urls,
        "total_pages": len(redacted_pages_urls),
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
