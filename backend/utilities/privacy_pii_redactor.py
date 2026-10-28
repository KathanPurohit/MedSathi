import io
import re
import sys
from PIL import Image, ImageDraw

# Optional OCR libraries imported safely at the top level
try:
    import pytesseract
except ImportError:
    pytesseract = None

if sys.platform == "win32":
    try:
        from winrt.windows.media.ocr import OcrEngine
        from winrt.windows.graphics.imaging import BitmapDecoder
        from winrt.windows.storage.streams import InMemoryRandomAccessStream, DataWriter
    except ImportError:
        OcrEngine = None
        BitmapDecoder = None
        InMemoryRandomAccessStream = None
        DataWriter = None
else:
    OcrEngine = None
    BitmapDecoder = None
    InMemoryRandomAccessStream = None
    DataWriter = None


PII_FIELD_PATTERNS = [
    ("name", 380),
    ("patient", 380),
    ("passport", 300),
    ("sex", 260),
    ("gender", 260),
    ("age", 260),
    ("aqe", 260),  # OCR typo for age
    ("dob", 260),
    ("date", 260),
    ("lab id", 300),
    ("uhid", 300),
    ("uhd", 300),  # OCR typo for uhid
    ("mrn", 300),
    ("phone", 320),
    ("mobile", 320),
    ("mob", 320),
    ("contact", 320),
    ("address", 420),
    ("client", 340),
    ("registration", 300),
    ("collected", 300),
    ("sample type", 260),
    ("specimen", 260),
    ("ref.", 320),
    ("referred", 320),
    ("refer", 320),
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

HEADER_EXCLUDE_TERMS = [
    "dr.", "doctor", "clinic", "hospital", "m.d.", "mbbs", "bams", "bhms",
    "internal medicine", "physician", "surgeon", "consultant", "healthcare",
    "nursing home", "polyclinic", "diagnostic", "reg. no", "reg no", "email",
    "opp.", "road", "street"
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


async def _run_winrt_ocr(image_bytes: bytes) -> list[OcrLine]:
    """Extracts OCR text lines using native Windows Media OCR API."""
    if not OcrEngine or not InMemoryRandomAccessStream:
        return []

    try:
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


def _run_tesseract_ocr(pil_img: Image.Image) -> list[OcrLine]:
    """Extracts OCR text lines using Tesseract engine (cross-platform / Linux Docker)."""
    if not pytesseract:
        return []

    try:
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
    except Exception:
        pass

    return []


async def _run_ocr(pil_img: Image.Image, image_bytes: bytes) -> list[OcrLine]:
    """Delegates OCR recognition to the best available engine for the current platform."""
    if sys.platform == "win32":
        lines = await _run_winrt_ocr(image_bytes)
        if lines:
            return lines

    return _run_tesseract_ocr(pil_img)


def _find_clinical_start_y(lines: list[OcrLine], img_height: int) -> int:
    """Calculates the vertical boundary where clinical prescriptions or lab results begin."""
    clinical_start_y = img_height

    for line in lines:
        if not line.words:
            continue

        line_lower = line.text.lower()
        # Avoid doctor qualifications or clinic header lines triggering clinical start
        if any(h in line_lower for h in HEADER_EXCLUDE_TERMS):
            continue

        y = line.words[0].bounding_rect.y
        if y < img_height * 0.15:
            continue

        is_clinical = False
        if any(term in line_lower for term in CLINICAL_TABLE_PATTERNS):
            is_clinical = True
        elif re.search(r"\b(rx|prescription|prescribed|medications?)\b", line_lower):
            is_clinical = True
        elif re.search(r"^\s*\d+[\.\)]\s*(?:tab|cap|syp|inj|oint|drop|tablet|capsule)\b", line_lower):
            is_clinical = True
        elif "result" in line_lower and any(w in line_lower for w in ["unit", "interval", "biological", "range"]):
            is_clinical = True

        if is_clinical:
            clinical_start_y = min(clinical_start_y, y)

    return clinical_start_y


def _redact_demographic_fields(
    draw: ImageDraw.ImageDraw,
    lines: list[OcrLine],
    ceiling_y: int,
    img_width: int,
    img_height: int,
) -> int:
    """Draws solid privacy bars over patient demographic labels and their corresponding values."""
    count = 0
    for line in lines:
        for w in line.words:
            r = w.bounding_rect
            if r.y >= ceiling_y:
                continue

            w_lower = w.text.lower().rstrip(":")
            for label, span_width in PII_FIELD_PATTERNS:
                if label == w_lower or (len(label) >= 4 and label in w_lower):
                    x0 = max(0, r.x - 4)
                    y0 = max(0, r.y - 4)
                    x1 = min(img_width, r.x + span_width)
                    y1 = min(img_height, r.y + r.height + 6)
                    draw.rectangle([x0, y0, x1, y1], fill="#0f172a")
                    count += 1
                    break
    return count


def _redact_identifiers_and_contacts(
    draw: ImageDraw.ImageDraw,
    lines: list[OcrLine],
    ceiling_y: int,
    img_width: int,
    img_height: int,
) -> int:
    """Blacks out remaining phone numbers, dates, emails, and alphanumeric IDs in the header."""
    count = 0
    for line in lines:
        for w in line.words:
            r = w.bounding_rect
            if r.y < ceiling_y:
                if (
                    re.search(r"\d{4,}|[0-9]+[xX]+|[xX]+[0-9]+|\d{1,2}[-\/][A-Za-z0-9]{3,}[-\/]\d{2,4}", w.text)
                    or "@" in w.text
                ):
                    draw.rectangle(
                        [
                            max(0, r.x - 6),
                            max(0, r.y - 4),
                            min(img_width, r.x + r.width + 6),
                            min(img_height, r.y + r.height + 6),
                        ],
                        fill="#0f172a",
                    )
                    count += 1
    return count


def _redact_qr_and_stamps(
    draw: ImageDraw.ImageDraw,
    lines: list[OcrLine],
    ceiling_y: int,
    img_width: int,
    img_height: int,
) -> int:
    """Blacks out verification barcodes, NABL emblems, and QR stamps in the header area."""
    count = 0
    for line in lines:
        for w in line.words:
            if w.bounding_rect.y < ceiling_y:
                if any(k in w.text.lower() for k in ["scan", "qr", "barcode", "nabl", "authenticity", "nau-"]):
                    draw.rectangle(
                        [
                            max(0, w.bounding_rect.x - 45),
                            max(0, w.bounding_rect.y - 50),
                            min(img_width, w.bounding_rect.x + 115),
                            min(img_height, w.bounding_rect.y + 60),
                        ],
                        fill="#0f172a",
                    )
                    count += 1
    return count


async def auto_redact_pii_from_image(image_bytes: bytes) -> bytes:
    """Coordinates detection and blacking out of patient demographics before AI processing."""
    try:
        pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception:
        return image_bytes

    draw = ImageDraw.Draw(pil_img)
    img_width, img_height = pil_img.size

    lines = await _run_ocr(pil_img, image_bytes)
    if not lines:
        return image_bytes

    # 1. Determine clinical boundary to protect prescriptions & lab results
    clinical_start_y = _find_clinical_start_y(lines, img_height)
    demographic_ceiling_y = min(clinical_start_y, int(img_height * 0.45))

    # 2. Delegate redaction tasks
    redacted_count = 0
    redacted_count += _redact_demographic_fields(draw, lines, demographic_ceiling_y, img_width, img_height)
    redacted_count += _redact_identifiers_and_contacts(draw, lines, demographic_ceiling_y, img_width, img_height)
    redacted_count += _redact_qr_and_stamps(draw, lines, demographic_ceiling_y, img_width, img_height)

    print(f"[Privacy Shield] Successfully blacked out {redacted_count} PII boxes from medical document.")
    output_buf = io.BytesIO()
    pil_img.save(output_buf, format="JPEG", quality=95)
    return output_buf.getvalue()
