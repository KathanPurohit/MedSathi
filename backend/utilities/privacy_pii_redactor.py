import io
import re
from PIL import Image, ImageDraw

PII_FIELD_PATTERNS = [
    ("name", 320),
    ("patient", 320),
    ("passport", 260),
    ("sex", 280),
    ("age", 280),
    ("gender", 280),
    ("dob", 240),
    ("lab id", 240),
    ("uhid", 220),
    ("mrn", 220),
    ("phone", 220),
    ("mobile", 220),
    ("contact", 220),
    ("address", 300),
    ("client", 280),
    ("registration", 240),
    ("collected", 240),
    ("sample type", 200),
]


async def _run_winrt_ocr(image_bytes: bytes):
    """Uses native Windows Media OCR to detect words and lines with bounding boxes."""
    try:
        from winrt.windows.media.ocr import OcrEngine
        from winrt.windows.graphics.imaging import BitmapDecoder
        from winrt.windows.storage.streams import InMemoryRandomAccessStream, DataWriter

        stream = InMemoryRandomAccessStream()
        writer = DataWriter(stream)
        writer.write_bytes(image_bytes)
        await writer.store_async()
        await writer.flush_async()
        stream.seek(0)

        decoder = await BitmapDecoder.create_async(stream)
        bitmap = await decoder.get_software_bitmap_async()
        engine = OcrEngine.try_create_from_user_profile_languages()
        if not engine:
            return []

        ocr_result = await engine.recognize_async(bitmap)
        return ocr_result.lines
    except Exception as exc:
        print(f"[Privacy Shield Error] WinRT OCR failed: {exc}")
        return []


async def auto_redact_pii_from_image(image_bytes: bytes) -> bytes:
    """Detects and draws black bars over patient demographics, names, IDs, and QR codes before AI processing."""
    try:
        pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception:
        return image_bytes

    draw = ImageDraw.Draw(pil_img)
    img_width, img_height = pil_img.size

    lines = await _run_winrt_ocr(image_bytes)
    if not lines:
        return image_bytes

    # 1. Determine where clinical tests or Rx prescriptions begin so medical data is preserved
    clinical_start_y = img_height
    for line in lines:
        line_lower = line.text.lower()
        if any(term in line_lower for term in [
            "complete blood", "rx", "investigation", "test name",
            "clinical", "biochemistry", "hematology", "pathology",
            "lipid profile", "thyroid profile", "liver function", "renal function"
        ]):
            clinical_start_y = min(clinical_start_y, line.words[0].bounding_rect.y)

    redacted_count = 0

    # 2. Black out PII fields in header area (label + value spanning to the right)
    for line in lines:
        for w in line.words:
            r = w.bounding_rect
            if r.y >= clinical_start_y:
                continue

            w_lower = w.text.lower()
            for label, span_width in PII_FIELD_PATTERNS:
                if label in w_lower:
                    x0 = max(0, r.x - 4)
                    y0 = max(0, r.y - 4)
                    x1 = min(img_width, r.x + span_width)
                    y1 = min(img_height, r.y + r.height + 6)
                    draw.rectangle([x0, y0, x1, y1], fill="#0f172a")
                    redacted_count += 1

    # 3. Black out any remaining ID numbers, phone numbers, or code identifiers in the header
    for line in lines:
        for w in line.words:
            r = w.bounding_rect
            if r.y < clinical_start_y:
                if re.search(r"\d{5,}|[0-9]+[xX]+|[xX]+[0-9]+", w.text):
                    draw.rectangle(
                        [max(0, r.x - 4), max(0, r.y - 4), min(img_width, r.x + r.width + 4), min(img_height, r.y + r.height + 4)],
                        fill="#0f172a"
                    )
                    redacted_count += 1

    # 4. Black out verification QR code / Barcode in top area
    for line in lines:
        line_lower = line.text.lower()
        if "qr code" in line_lower or "authenticity" in line_lower or "barcode" in line_lower:
            r = line.words[0].bounding_rect
            draw.rectangle(
                [max(0, r.x - 130), max(0, r.y - 150), min(img_width, r.x + 200), min(img_height, r.y + 10)],
                fill="#0f172a"
            )
            redacted_count += 1

    print(f"[Privacy Shield] Successfully blacked out {redacted_count} PII boxes from medical document.")
    output_buf = io.BytesIO()
    pil_img.save(output_buf, format="JPEG", quality=95)
    return output_buf.getvalue()
