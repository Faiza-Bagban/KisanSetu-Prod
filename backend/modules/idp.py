"""
idp.py  –  Intelligent Document Processor
Supports English + Marathi (Devanagari) documents, images and PDFs.

Fixes vs original
─────────────────
1. UnboundLocalError  →  `candidate` scoped correctly inside name_match block
2. Broken Devanagari regex  →  full Unicode block \\u0900-\\u097F used everywhere
3. OCR accuracy  →  2× upscale + Otsu/adaptive dual-path + multi-PSM voting
4. Marathi field patterns  →  नाव, जन्म तारीख, वडिलांचे नाव, जात, गोत्र, …
5. PDF quality  →  convert_from_path at 250 DPI
6. Table / land-record extraction  →  pixel-aligned row grouping + KV parser

v2 fixes (from live test run)
──────────────────────────────
7. Degraded separator  →  patterns accept '.' and ';' beside ':' and '-'
8. Marathi name fallback  →  derive name from KV pairs when regex fails
9. False-positive address  →  reject single-word label-only values
10. kv_pairs UnboundLocalError  →  fallback blocks moved after step 5

v3 fixes (from live test run #2)
──────────────────────────────────
11. Wrong name from garbled family-key (marathi_image) →
    KV-pair name fallback now rejects keys that start with a Latin character.
    Root cause: "आईचे नाव" was OCR'd as "ange नाव"; "ange नाव" contained "नाव"
    and passed the family-key check, causing the mother's name to become the
    subject's. Fix: standalone नाव/Name key must start with Devanagari OR be
    a plain ASCII word — never Latin-prefix + Devanagari.
12. Address "काळजी" false-positive (Form_1-MR) →
    Post-validate: extracted address cleared when it has < 2 words.
    Root cause: "काळजी" is exactly 5 Unicode chars, slipping the {5,} guard.
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import re
import numpy as np
import cv2
import pytesseract
from pdf2image import convert_from_path

from modules.confidence import compute_confidence
from modules.matcher import find_best_match

# ── Tesseract executable ──────────────────────────────────────────────────────
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ── Character class constants ─────────────────────────────────────────────────
DEVA   = r'\u0900-\u097F'          # full Devanagari Unicode block
LATIN  = r'A-Za-z'
DIGITS = r'0-9\u0966-\u096F'       # ASCII + Devanagari digits
NAME_CHARS = rf'[{LATIN}{DEVA} \-\.]+'

# ── Field extraction patterns (English + Marathi) ─────────────────────────────
#
#  Each key maps to a list of regex patterns tried in order.
#  Group 1 is the captured value in every pattern.
#
PATTERNS: dict[str, list[str]] = {

    # ── Core Aadhaar / common fields ──────────────────────────────────────────
    # SEP = separators: colon, hyphen, period (degraded OCR), semicolon (degraded OCR)
    "name": [
        rf'(?:Name|नाव)\s*[:\-\.;]\s*({NAME_CHARS})',
    ],
    "dob": [
        rf'(?:Date\s*of\s*Birth|DOB|जन्म\s*तारीख)\s*[:\-\.;]\s*([{DIGITS} /\-\.]+)',
    ],
    "gender": [
        rf'(?:Gender|लिंग)\s*[:\-\.;]\s*([{LATIN}{DEVA}]+)',
    ],
    "mobile": [
        r'(?:Mobile|मोबाईल\s*(?:क्रमांक|नंबर)?)\s*[:\-\.;]?\s*(\+?[\d\s\-]{8,15})',
    ],
    "aadhaar": [
        r'\b(\d{4}\s?\d{4}\s?\d{4})\b',
    ],

    # ── Land / agriculture records ────────────────────────────────────────────
    "land_id": [
        # '.' separator handles degraded OCR: "Survey. MH-1234" → was missed before
        r'(?:Survey|Plot|Land|सर्वेक्षण|गट\s*क्रमांक|खाते\s*क्रमांक)\s*[:\-\.;#]?\s*([A-Z0-9\-/]+)',
    ],
    "village": [
        rf'(?:Village|गाव)\s*[:\-\.;]\s*({NAME_CHARS})',
    ],
    "taluka": [
        rf'(?:Taluka|तालुका)\s*[:\-\.;]\s*({NAME_CHARS})',
    ],
    "district": [
        rf'(?:District|जिल्हा)\s*[:\-\.;]\s*({NAME_CHARS})',
    ],

    # ── Marathi biodata / personal fields ─────────────────────────────────────
    "birth_time": [
        rf'(?:जन्म\s*वेळ|Birth\s*Time)\s*[:\-\.;]\s*([{DIGITS}:\s]+(?:AM|PM)?)',
    ],
    "birth_place": [
        rf'(?:जन्म\s*ठिकाण|Birth\s*Place)\s*[:\-\.;]\s*({NAME_CHARS})',
    ],
    "caste": [
        rf'(?:जात|Caste)\s*[:\-\.;]\s*({NAME_CHARS})',
    ],
    "gotra": [
        rf'(?:गोत्र|Gotra)\s*[:\-\.;]\s*({NAME_CHARS})',
    ],
    "height": [
        rf'(?:उंची|Height)\s*[:\-\.;]\s*([{LATIN}{DEVA}{DIGITS}\s\.]+)',
    ],
    "occupation": [
        rf'(?:व्यवसाय|Occupation)\s*[:\-\.;]\s*({NAME_CHARS})',
    ],
    "father_name": [
        rf'(?:वडिलांचे\s*नाव|Father(?:\'s)?\s*Name)\s*[:\-\.;]\s*({NAME_CHARS})',
    ],
    "mother_name": [
        rf'(?:आईचे\s*नाव|आईचं\s*नाव|Mother(?:\'s)?\s*Name)\s*[:\-\.;]\s*({NAME_CHARS})',
    ],
    "brother": [
        rf'(?:भाऊ|Brother)\s*[:\-\.;]\s*({NAME_CHARS})',
    ],
    "sister": [
        rf'(?:बहीण|Sister)\s*[:\-\.;]\s*({NAME_CHARS})',
    ],
    "father_occupation": [
        rf'(?:वडिलांचा\s*व्यवसाय|वडिलांचा)\s*[:\-\.;]\s*([{LATIN}{DEVA}\s]+)',
    ],
    "address": [
        rf'(?:पत्ता|Address)\s*[:\-\.;]\s*([{LATIN}{DEVA}\d,\s/\-]{{5,}})',
        # min 5 chars to avoid capturing just the label word "काळजी"
    ],
}


# ══════════════════════════════════════════════════════════════════════════════
#  IMAGE PREPROCESSING
# ══════════════════════════════════════════════════════════════════════════════

def _upscale(img: np.ndarray, factor: int = 2) -> np.ndarray:
    """Bicubic upscale – improves OCR on small / low-DPI inputs."""
    h, w = img.shape[:2]
    return cv2.resize(img, (w * factor, h * factor),
                      interpolation=cv2.INTER_CUBIC)


def preprocess_advanced(img: np.ndarray,
                        scale: int = 2
                        ) -> tuple[np.ndarray, np.ndarray]:
    """
    Return TWO preprocessed variants (Otsu + Adaptive) so the caller can
    pick the one that yields richer OCR text.

    Pipeline
    --------
    1. Optional upscale  (critical for sub-200 DPI inputs)
    2. Grayscale
    3. Fast NL-Means denoise
    4. CLAHE contrast enhancement
    5. Unsharp-mask sharpening  (helps Devanagari matras)
    6. Otsu global threshold
    7. Adaptive Gaussian threshold
    8. Morphological closing on both  (reconnects broken strokes)
    """
    if scale > 1:
        img = _upscale(img, scale)

    # Convert to gray if needed
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img

    # Denoise
    denoised = cv2.fastNlMeansDenoising(gray, h=10)

    # CLAHE (higher clipLimit helps faded ink)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    contrast = clahe.apply(denoised)

    # Unsharp mask – accentuates thin Devanagari strokes
    sharp_kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    sharpened = cv2.filter2D(contrast, -1, sharp_kernel)

    # ── Binarisation path A: Otsu (best for clean / uniform background)
    _, otsu = cv2.threshold(sharpened, 0, 255,
                            cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # ── Binarisation path B: Adaptive Gaussian (best for uneven lighting)
    adaptive = cv2.adaptiveThreshold(
        sharpened, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 15, 8
    )

    # Morphological closing joins broken letter segments
    kernel = np.ones((2, 2), np.uint8)
    otsu_closed     = cv2.morphologyEx(otsu,     cv2.MORPH_CLOSE, kernel)
    adaptive_closed = cv2.morphologyEx(adaptive, cv2.MORPH_CLOSE, kernel)

    return otsu_closed, adaptive_closed


# ══════════════════════════════════════════════════════════════════════════════
#  OCR RUNNER
# ══════════════════════════════════════════════════════════════════════════════

def _run_ocr_single(img: np.ndarray, psm: int, lang: str = "eng+mar") -> str:
    cfg = rf"--oem 3 --psm {psm}"
    try:
        return pytesseract.image_to_string(img, lang=lang, config=cfg)
    except Exception:
        return ""


def run_ocr(img: np.ndarray, lang: str = "eng+mar") -> str:
    """
    Try PSM 6 (uniform block), 3 (auto), 4 (single column) and return
    the result with the most non-whitespace characters.
    """
    best = ""
    for psm in (6, 3, 4):
        result = _run_ocr_single(img, psm, lang)
        if len(result.strip()) > len(best.strip()):
            best = result
    return best


def ocr_best_of_two(otsu: np.ndarray,
                    adaptive: np.ndarray,
                    lang: str = "eng+mar") -> str:
    """
    Run OCR on both preprocessed variants and return whichever produced
    more text (a simple but effective heuristic).
    """
    t1 = run_ocr(otsu,     lang)
    t2 = run_ocr(adaptive, lang)
    return t1 if len(t1.strip()) >= len(t2.strip()) else t2


# ══════════════════════════════════════════════════════════════════════════════
#  TABLE / KEY-VALUE EXTRACTION
# ══════════════════════════════════════════════════════════════════════════════

def extract_table_data(img: np.ndarray) -> list[str]:
    """
    Group Tesseract word tokens by (block, paragraph, line) to reconstruct
    logical rows – works for tables as well as labelled forms.
    """
    data = pytesseract.image_to_data(
        img,
        output_type=pytesseract.Output.DICT,
        config=r"--oem 3 --psm 6",
        lang="eng+mar",
    )
    rows: dict[tuple, list[str]] = {}
    for i, text in enumerate(data["text"]):
        text = text.strip()
        if not text:
            continue
        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        rows.setdefault(key, []).append(text)

    return [" ".join(words) for words in rows.values()]


def extract_kv_pairs(text: str) -> list[tuple[str, str]]:
    """
    Parse key-value rows of the form  'Label : Value'  or  'Label - Value'.
    This handles:
      • Aadhaar form fields
      • Marathi biodata lines  (नाव : मितेन मियाणी)
      • Land-record entries    (गट क्रमांक : 123/A)
    Returns a list of (label, value) tuples.
    """
    pairs: list[tuple[str, str]] = []
    pattern = re.compile(
        rf'^([{LATIN}{DEVA}\s/]+?)\s*[:\-]\s*'
        rf'([{LATIN}{DEVA}\d\s/\.,\-\u0966-\u096F]+)$',
        re.UNICODE
    )
    for line in text.splitlines():
        m = pattern.match(line.strip())
        if m:
            k, v = m.group(1).strip(), m.group(2).strip()
            if k and v and len(k) > 1:
                pairs.append((k, v))
    return pairs


def extract_land_table(kv_pairs: list[tuple[str, str]]) -> dict:
    """
    From the generic KV pairs pick out land-record specific fields and
    return them in a structured dict.
    """
    LAND_KEYS = {
        # Marathi label → internal key
        "गट क्रमांक":      "plot_number",
        "खाते क्रमांक":    "account_number",
        "सर्वेक्षण":       "survey_number",
        "गाव":             "village",
        "तालुका":          "taluka",
        "जिल्हा":          "district",
        "क्षेत्र":         "area",
        "खातेदार":         "owner_name",
        "survey":          "survey_number",
        "plot":            "plot_number",
        "village":         "village",
        "district":        "district",
    }
    result: dict = {}
    for label, value in kv_pairs:
        for key_fragment, field_name in LAND_KEYS.items():
            if key_fragment.lower() in label.lower():
                result[field_name] = value
                break
    return result


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN FIELD EXTRACTOR
# ══════════════════════════════════════════════════════════════════════════════

def extract_fields(file_path: str) -> dict:
    """
    Entry point – accepts any image format or PDF.
    Returns a structured result dict with extracted fields, confidence
    scores, DB match info, KV pairs, land-record table, and a status flag.
    """

    # ── 1. Load and OCR ───────────────────────────────────────────────────────
    if file_path.lower().endswith(".pdf"):
        # Higher DPI → better detail for Devanagari glyphs
        pages = convert_from_path(file_path, dpi=250)
        full_text, all_rows = "", []
        for page in pages:
            img_rgb  = np.array(page)
            img_bgr  = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
            otsu, adaptive = preprocess_advanced(img_bgr, scale=1)  # already 250 DPI
            full_text += "\n" + ocr_best_of_two(otsu, adaptive)
            all_rows.extend(extract_table_data(otsu))
        text       = full_text
        table_data = all_rows

    else:
        img = cv2.imread(file_path)
        if img is None:
            raise ValueError(f"Cannot read file: {file_path}")
        otsu, adaptive = preprocess_advanced(img, scale=2)
        text       = ocr_best_of_two(otsu, adaptive)
        table_data = extract_table_data(otsu)

    print("\n🔍 OCR TEXT:\n", text)

    # ── 2. Regex field extraction ─────────────────────────────────────────────
    extracted: dict[str, str | None] = {}
    for field, patterns in PATTERNS.items():
        extracted[field] = None
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE | re.UNICODE | re.MULTILINE)
            if m:
                extracted[field] = m.group(1).strip()
                break

    # ── 2b. Post-validate address ─────────────────────────────────────────────
    # A genuine address contains at least 2 words. Single-word matches are
    # just the field label itself (e.g. blank Aadhaar form's "काळजी" label).
    if extracted.get("address") and len(extracted["address"].split()) < 2:
        extracted["address"] = None

    # ── 3. Validate name (regex result only) ─────────────────────────────────
    name = extracted.get("name")
    if not is_valid_name(name):
        name = None

    # ── 4. Validate Aadhaar ───────────────────────────────────────────────────
    aadhaar_raw  = extracted.get("aadhaar")
    aadhaar_digits: str | None = None
    aadhaar_display: str | None = None
    if aadhaar_raw:
        aadhaar_digits = re.sub(r"\D", "", aadhaar_raw)[:12]
        if len(aadhaar_digits) >= 4:
            aadhaar_display = f"XXXX-XXXX-{aadhaar_digits[-4:]}"

    # ── 5. KV pairs + land table ──────────────────────────────────────────────
    kv_pairs   = extract_kv_pairs(text)
    land_table = extract_land_table(kv_pairs)

    # Also try to fill land_id from land_table if regex missed it
    land_id = extracted.get("land_id") or land_table.get("plot_number") or \
              land_table.get("survey_number") or land_table.get("account_number")

    # ── 5b. Name fallback: scan KV pairs for a bare "नाव" / "Name" key ────────
    #
    # kv_pairs is now available. When OCR garbles the नाव line (ornamental
    # biodata backgrounds), the regex in step 2 returns nothing. But
    # extract_kv_pairs() often still grabs the value because the colon is
    # visible even when the label chars are mangled.
    # We look for any KV pair whose KEY contains "नाव" / "name" but is NOT a
    # family-member key (वडिलांचे, आईचे, भाऊ, बहीण …).
    #
    FAMILY_KEYS = {"वडिलांचे", "आईचे", "आईचं", "भाऊ", "बहीण",
                   "brother", "sister", "father", "mother"}
    if name is None:
        for label, value in kv_pairs:
            label_lower = label.lower()
            if "नाव" in label or "name" in label_lower:
                # Guard: reject garbled keys like "ange नाव" (OCR of "आईचे नाव")
                # A genuine standalone नाव/Name key must start with a Devanagari
                # char OR be the plain ASCII word "name" — never a Latin prefix
                # followed by a Devanagari word.
                label_stripped = label.strip()
                first_char = label_stripped[0] if label_stripped else ""
                is_deva_start  = "\u0900" <= first_char <= "\u097F"
                is_plain_latin = re.fullmatch(r"[A-Za-z]+", label_stripped) is not None
                if not (is_deva_start or is_plain_latin):
                    # Mixed / garbled key — skip it
                    continue
                if not any(fk in label for fk in FAMILY_KEYS):
                    if is_valid_name(value):
                        name = value
                        break

    # ── 5c. Last-resort: infer shared family surname ──────────────────────────
    #
    # If name is still None but we have family-member names (father, mother,
    # sibling), the most common trailing word is almost certainly the shared
    # surname — useful as a DB fuzzy-match hint even when the first name is
    # unrecoverable from the garbled OCR line.
    #
    if name is None:
        from collections import Counter
        family_values: list[str] = [
            v for v in [
                extracted.get("father_name"),
                extracted.get("mother_name"),
                extracted.get("brother"),
                extracted.get("sister"),
            ] if v
        ]
        # Also harvest family values directly from kv_pairs
        for label, value in kv_pairs:
            if any(fk in label for fk in FAMILY_KEYS):
                family_values.append(value)

        surnames = [
            parts[-1]
            for fv in family_values
            if (parts := fv.strip().split()) and len(parts) >= 2
        ]
        if surnames:
            common_surname = Counter(surnames).most_common(1)[0][0]
            extracted["inferred_surname"] = common_surname

    # ── 6. Assemble result ────────────────────────────────────────────────────
    additional = {
        k: v for k, v in extracted.items()
        if k not in ("name", "land_id", "aadhaar") and v
    }
    # Surface inferred_surname even though it's not a "real" extracted field
    if extracted.get("inferred_surname"):
        additional["inferred_surname"] = extracted["inferred_surname"]

    result: dict = {
        "name": {
            "value":      name,
            "confidence": compute_confidence("name", name, text),
        },
        "land_id": {
            "value":      land_id,
            "confidence": compute_confidence("land_id", land_id, text),
        },
        "aadhaar": {
            "value":      aadhaar_display,
            "confidence": compute_confidence("aadhaar", aadhaar_digits, text),
        },
        "additional_fields": additional,  # dob, gender, caste, gotra, …
        "kv_pairs":    kv_pairs,          # raw label→value pairs from document
        "land_table":  land_table,        # structured land-record fields
        "table_data":  table_data,        # raw OCR row tokens
    }

    # ── 7. DB match for name ──────────────────────────────────────────────────
    if name:
        best_match, score = find_best_match(name)
        result["name"]["matched_with"] = best_match
        result["name"]["db_match"]     = score
        result["name"]["flagged"]      = score < 75

    # ── 8. Auto-verify status ─────────────────────────────────────────────────
    required_fields = ("name", "land_id", "aadhaar")
    missing  = any(result[f]["value"] is None for f in required_fields)
    valid_fs = [result[f] for f in required_fields if result[f]["value"]]
    flagged  = result["name"].get("flagged", False)

    if (not missing
            and not flagged
            and all(v["confidence"] >= 75 for v in valid_fs)):
        result["status"] = "AUTO-VERIFIED"
    else:
        result["status"] = "REVIEW REQUIRED"

    return result


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def is_valid_name(name: str | None) -> bool:
    """
    Returns True only when `name` looks like a genuine personal name
    (at least two words, contains letters, is not just the field label).
    """
    if not name:
        return False
    # Reject if the value IS the label word itself
    if re.fullmatch(
        rf'(?:Name|नाव)\s*',
        name,
        re.IGNORECASE | re.UNICODE
    ):
        return False
    # Must contain at least one letter (Latin or Devanagari)
    if not re.search(rf'[{LATIN}{DEVA}]', name, re.UNICODE):
        return False
    # Must be at least two tokens (first + last name)
    if len(name.split()) < 2:
        return False
    return True


# ══════════════════════════════════════════════════════════════════════════════
#  INTERACTIVE DEMO
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
    IMAGE_DIR = os.path.join(BASE_DIR, "..")

    print("\nAvailable test images:")
    print(
        "clean.jpg, partial.jpg, degraded.jpg, variation.jpg, fraud.jpg, "
        "sample.pdf, marathi.pdf, Form_1-MR.pdf, marathi_image.jpeg\n"
    )

    img_name   = input("Enter image/pdf name: ").strip()
    image_path = os.path.join(IMAGE_DIR, img_name)

    output = extract_fields(image_path)

    print("\n✅ RESULT:")
    import json

    # Pretty-print everything except table_data (can be huge)
    display = {k: v for k, v in output.items() if k != "table_data"}
    print(json.dumps(display, ensure_ascii=False, indent=2))
    print(f"\n  table_data: [{len(output['table_data'])} rows]")