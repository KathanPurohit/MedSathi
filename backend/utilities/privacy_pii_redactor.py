import asyncio
import io
import re
from PIL import Image, ImageDraw

PII_KEYWORDS = [
    "name", "patient", "pt name", "sex", "age", "gender", "dob",
    "passport", "lab id", "ref. id", "ref by", "uhid", "mrn",
    "phone", "mobile", "contact", "client name", "address",
    "sample id", "barcode", "collected at", "registration on"
]


async def _run_winrt_ocr_boxes(image_bytes: bytes):
    """Uses native Windows Media OCR to detect bounding boxes of text."""
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
    except Exception:
        return []


def auto_redact_pii_from_image(image_bytes: bytes) -> bytes:
    """Automatically detects and blacks out patient PII (names, IDs, phone numbers) from image bytes."""
    try:
        pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception:
        return image_bytes

    draw = ImageDraw.Draw(pil_img)
    img_width, img_height = pil_img.size

    # Run native offline OCR
    try:
        lines = asyncio.run(_run_winrt_ocr_boxes(image_bytes))
    except Exception:
        lines = []

    redacted = False

    if lines:
        for line in lines:
            line_text_lower = line.text.lower()
            is_pii_keyword = any(kw in line_text_lower for kw in PII_KEYWORDS)
            has_phone_or_id = bool(re.search(r"(\+?91[\-\s]?)?[6-9]\d{9}|\b\d{6,12}\b", line.text))

            if is_pii_keyword or has_phone_or_id:
                # Black out each word on the PII line
                for word in line.words:
                    r = word.bounding_rect
                    # Add 4px padding around each word for complete coverage
                    x0 = max(0, r.x - 3)
                    y0 = max(0, r.y - 3)
                    x1 = min(img_width, r.x + r.width + 3)
                    y1 = min(img_height, r.y + r.height + 3)
                    draw.rectangle([x0, y0, x1, y1], fill="#0f172a")
                    redacted = True

    # Also blackout standard top-right QR code / barcode region if present in header
    # (top 15% height, right 40% width often contains patient verification QR code)
    # We black out words matching QR code prompt
    if lines:
        for line in lines:
            if "qr code" in line.text.lower() or "authenticity" in line.text.lower():
                r_line = line.words[0].bounding_rect
                # Black out QR code area above the line
                draw.rectangle(
                    [max(0, r_line.x - 100), max(0, r_line.y - 120), min(img_width, r_line.x + 150), r_line.y],
                    fill="#0f172a"
                )
                redacted = True

    output_buf = io.BytesIO()
    pil_img.save(output_buf, format="JPEG", quality=92)
    return output_buf.getvalue()
