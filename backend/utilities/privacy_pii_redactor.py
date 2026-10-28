import io
import re
from PIL import Image, ImageDraw

PII_FIELD_PATTERNS = [
    ("name", 380),
    ("patient", 380),
    ("passport", 300),
    ("sex", 300),
    ("gender", 300),
    ("age", 300),
    ("aqe", 300),  # OCR typo for age
    ("dob", 280),
    ("lab id", 300),
    ("uhid", 280),
    ("mrn", 280),
    ("phone", 300),
    ("mobile", 300),
    ("contact", 300),
    ("address", 420),
    ("client", 340),
    ("registration", 300),
    ("collected", 300),
    ("sample type", 260),
    ("specimen", 260),
    ("ref.", 350),
    ("doctor", 350),
    ("dr.", 350),
    ("consultant", 350),
    ("approved", 300),
    ("printed", 300),
    ("status", 300),
]

CLINICAL_TABLE_PATTERNS = [
    "complete blood", "cbc", "haemogram", "investigation", "test name",
    "lipid profile", "thyroid profile", "liver function", "renal function", "kidney function",
    "urine routine", "urine examination", "differential count",
    "biological ref", "reference interval", "ref. interval", "ref interval",
    "test parameter", "observed value"
]


class OcrBoundingRect:
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x = x
        self.y = y
        self.width = width
        self.height = height


class OcrWord:
    def __init__(self, text: str, bounding_rect: OcrBoundingRect):
        self.text = text
        self.bounding_rect = bounding_rect


class OcrLine:
    def __init__(self, text: str, words: list[OcrWord]):
        self.text = text
        self.words = words


async def _run_ocr(pil_img: Image.Image, image_bytes: bytes) -> list[OcrLine]:
    """Runs OCR using Tesseract (cross-platform / Linux Docker) with WinRT fallback on Windows."""
    # 1. Try Tesseract first (primary cross-platform engine)
    try:
        import pytesseract

        data = pytesseract.image_to_data(pil_img, output_type=pytesseract.Output.DICT)
        lines_dict: dict[tuple, list[OcrWord]] = {}
        total_items = len(data.get("text", []))

        for i in range(total_items):
            text = str(data["text"][i]).strip()
            if not text:
                continue

            line_key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
            word = OcrWord(
                text=text,
                bounding_rect=OcrBoundingRect(
                    x=int(data["left"][i]),
                    y=int(data["top"][i]),
                    width=int(data["width"][i]),
                    height=int(data["height"][i]),
                ),
            )
            lines_dict.setdefault(line_key, []).append(word)

        if lines_dict:
            return [
                OcrLine(text=" ".join(w.text for w in words), words=words)
                for words in lines_dict.values()
            ]
    except Exception as tesseract_err:
        # If tesseract is not installed or fails, try WinRT fallback on Windows
        pass

    # 2. Fallback to native Windows OCR if available
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
        winrt_lines: list[OcrLine] = []
        for line in ocr_result.lines:
            words = [
                OcrWord(
                    text=w.text,
                    bounding_rect=OcrBoundingRect(
                        x=int(w.bounding_rect.x),
                        y=int(w.bounding_rect.y),
                        width=int(w.bounding_rect.width),
                        height=int(w.bounding_rect.height),
                    ),
                )
                for w in line.words
            ]
            winrt_lines.append(OcrLine(text=line.text, words=words))
        return winrt_lines
    except Exception:
        return []


async def auto_redact_pii_from_image(image_bytes: bytes) -> bytes:
    """Detects and draws black bars over patient demographics, names, IDs, and QR codes before AI processing."""
    try:
        pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception:
        return image_bytes

    draw = ImageDraw.Draw(pil_img)
    img_width, img_height = pil_img.size

    lines = await _run_ocr(pil_img, image_bytes)
    if not lines:
        return image_bytes

    # 1. Determine where clinical tests or Rx prescriptions begin so medical data is preserved
    clinical_start_y = img_height
    for line in lines:
        line_lower = line.text.lower()
        y = line.words[0].bounding_rect.y

        is_clinical = False
        if any(term in line_lower for term in CLINICAL_TABLE_PATTERNS):
            is_clinical = True
        elif re.search(r"\b(rx|prescription|medicines?|tablets?)\b", line_lower):
            is_clinical = True
        elif "result" in line_lower and any(w in line_lower for w in ["unit", "interval", "biological", "range"]):
            is_clinical = True

        if is_clinical:
            clinical_start_y = min(clinical_start_y, y)

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
                    break

    # 3. Black out any remaining ID numbers, phone numbers, or code identifiers in the header
    for line in lines:
        for w in line.words:
            r = w.bounding_rect
            if r.y < clinical_start_y:
                if re.search(r"\d{4,}|[0-9]+[xX]+|[xX]+[0-9]+|\d{1,2}-[A-Za-z]{3}-\d{2,4}", w.text):
                    draw.rectangle(
                        [max(0, r.x - 6), max(0, r.y - 4), min(img_width, r.x + r.width + 6), min(img_height, r.y + r.height + 6)],
                        fill="#0f172a"
                    )
                    redacted_count += 1

    # 4. Black out verification QR code / Barcode in top area
    for line in lines:
        for w in line.words:
            if w.bounding_rect.y < clinical_start_y:
                if any(k in w.text.lower() for k in ["mc-2202", "nabl", "scan", "qr", "barcode", "authenticity"]):
                    draw.rectangle(
                        [max(0, w.bounding_rect.x - 170), max(0, w.bounding_rect.y - 95), min(img_width, w.bounding_rect.x + 20), min(img_height, w.bounding_rect.y + 15)],
                        fill="#0f172a"
                    )
                    redacted_count += 1

    print(f"[Privacy Shield] Successfully blacked out {redacted_count} PII boxes from medical document.")
    output_buf = io.BytesIO()
    pil_img.save(output_buf, format="JPEG", quality=95)
    return output_buf.getvalue()
