import asyncio
import base64
import io
import logging
from typing import Any
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel
from PIL import Image
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
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers ensuring CORS headers are ALWAYS present on error responses
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc)},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Unhandled server error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Server processing error: {str(exc)}"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        },
    )


@app.get("/")
def root():
    return {"status": "ok", "service": "MedSaathi API"}


@app.get("/health")
def health():
    return {"status": "healthy"}


class VoiceGenerateRequest(BaseModel):
    voice_script: str
    language: str = "English"
    voice_gender: str = "female"


def _validate_and_extract_pages(raw_bytes: bytes, filename: str | None, content_type: str | None) -> list[bytes]:
    """Validates document format and renders single or multi-page documents to high-resolution JPEG bytes."""
    is_pdf = (
        raw_bytes.startswith(b"%PDF")
        or (content_type and "pdf" in content_type.lower())
        or (filename and filename.lower().endswith(".pdf"))
    )
    is_image = (
        (content_type and content_type.startswith("image/"))
        or (filename and any(filename.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp"]))
        or not is_pdf
    )

    if is_pdf:
        try:
            pdf = pdfium.PdfDocument(raw_bytes)
            page_count = len(pdf)
            print(f"[Document Engine] Detected PDF with {page_count} page(s).")
            rendered_pages: list[bytes] = []
            # Cap at 4 pages on free cloud tier to protect memory and responsiveness
            max_pages = min(page_count, 4)
            for i in range(max_pages):
                page = pdf[i]
                # Scale 1.2 provides optimal OCR/Gemini reading without RAM bloat
                pil_page = page.render(scale=1.2).to_pil().convert("RGB")
                if max(pil_page.size) > 1400:
                    pil_page.thumbnail((1400, 1400), Image.Resampling.LANCZOS)
                buf = io.BytesIO()
                pil_page.save(buf, format="JPEG", quality=80, optimize=True)
                rendered_pages.append(buf.getvalue())
            return rendered_pages
        except Exception as exc:
            logging.error(f"Error parsing PDF document: {exc}")
            raise HTTPException(status_code=400, detail=f"Failed to read PDF document: {exc}")

    # Standard image handling
    try:
        im = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
        if max(im.size) > 1600:
            im.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=82, optimize=True)
        return [buf.getvalue()]
    except Exception as exc:
        logging.error(f"Error reading image: {exc}")
        raise HTTPException(status_code=400, detail="Please upload a valid image file (JPEG, PNG, WEBP) or PDF document.")


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
    """Packages the analysis results and compact preview data URLs for client presentation."""
    # Compress preview images (max 800px, quality 75) so response JSON is lightweight (<100KB)
    preview_urls: list[str] = []
    for b in sanitized_pages:
        try:
            im = Image.open(io.BytesIO(b))
            if max(im.size) > 800:
                im.thumbnail((800, 800), Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            im.save(buf, format="JPEG", quality=75, optimize=True)
            preview_urls.append(f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode('utf-8')}")
        except Exception:
            preview_urls.append(f"data:image/jpeg;base64,{base64.b64encode(b).decode('utf-8')}")

    return {
        "redacted_image_data_url": preview_urls[0] if preview_urls else "",
        "redacted_pages": preview_urls,
        "total_pages": len(preview_urls),
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

    is_pdf = (
        raw_bytes.startswith(b"%PDF")
        or b"%PDF" in raw_bytes[:1024]
        or (file.content_type and "pdf" in file.content_type.lower())
        or (file.filename and file.filename.lower().endswith(".pdf"))
    )

    if is_pdf:
        # Non-blocking concurrent execution: Gemini extraction and PDF thumbnail generation run simultaneously
        async def _extract_report():
            return await asyncio.to_thread(_extract_report_with_resilience, [raw_bytes], language)

        async def _render_preview():
            def _render():
                try:
                    pdf = pdfium.PdfDocument(raw_bytes)
                    if len(pdf) == 0:
                        return None
                    first_page = pdf[0].render(scale=1.2).to_pil().convert("RGB")
                    if max(first_page.size) > 1000:
                        first_page.thumbnail((1000, 1000), Image.Resampling.LANCZOS)
                    buf = io.BytesIO()
                    first_page.save(buf, format="JPEG", quality=80, optimize=True)
                    return buf.getvalue()
                except Exception as exc:
                    logging.warning(f"Could not render PDF preview thumbnail: {exc}")
                    return None

            thumb_bytes = await asyncio.to_thread(_render)
            if thumb_bytes:
                redacted_thumb = await auto_redact_pii_from_image(thumb_bytes)
                return [redacted_thumb]
            return []

        report, sanitized_pages_bytes = await asyncio.gather(_extract_report(), _render_preview())
    else:
        # 1. Render all document pages with safe memory bounds (non-blocking)
        page_images_bytes = await asyncio.to_thread(
            _validate_and_extract_pages, raw_bytes, file.filename, file.content_type
        )

        # 2. Blackout patient demographics and identifiers (with timeout protection)
        sanitized_pages_bytes = await _redact_document_pages(page_images_bytes)

        # 3. Multimodal vision extraction via Gemini (non-blocking)
        report = await asyncio.to_thread(_extract_report_with_resilience, sanitized_pages_bytes, language)

    # 4. Generic pricing & savings matching (non-blocking)
    def _do_match(meds):
        return match_generic_salt_prices(meds)

    generic_savings, total_monthly_saved = await asyncio.to_thread(_do_match, report.medicines)
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

    # 7. Package and serialize response with compact previews
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
