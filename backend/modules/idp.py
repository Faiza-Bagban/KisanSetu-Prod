"""
idp.py  –  Intelligent Document Processor
Supports English + Marathi (Devanagari) documents, images and PDFs.

Week 2, Day 1 (Sakshi) — Script auto-detect added: detect_script()/
pick_lang_pack() run a cheap first-pass OCR to sample the character script,
then pick the right Tesseract lang pack ("eng" vs "eng+mar") for the real
extraction pass, instead of always forcing "eng+mar" on every document.
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

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

DEVA   = r'\u0900-\u097F'
LATIN  = r'A-Za-z'
DIGITS = r'0-9\u0966-\u096F'
NAME_CHARS = rf'[{LATIN}{DEVA} \-\.]+'

PATTERNS: dict[str, list[str]] = {
    "name": [rf'(?:Name|नाव)\s*[:\-\.;]\s*({NAME_CHARS})'],
    "dob": [rf'(?:Date\s*of\s*Birth|DOB|जन्म\s*तारीख)\s*[:\-\.;]\s*([{DIGITS} /\-\.]+)'],
    "gender": [rf'(?:Gender|लिंग)\s*[:\-\.;]\s*([{LATIN}{DEVA}]+)'],
    "mobile": [r'(?:Mobile|मोबाईल\s*(?:क्रमांक|नंबर)?)\s*[:\-\.;]?\s*(\+?[\d\s\-]{8,15})'],
    "aadhaar": [r'\b(\d{4}\s?\d{4}\s?\d{4})\b'],
    "land_id": [r'(?:Survey|Plot|Land|सर्वेक्षण|गट\s*क्रमांक|खाते\s*क्रमांक)\s*[:\-\.;#]?\s*([A-Z0-9\-/]+)'],
    "village": [rf'(?:Village|गाव)\s*[:\-\.;]\s*({NAME_CHARS})'],
    "taluka": [rf'(?:Taluka|तालुका)\s*[:\-\.;]\s*({NAME_CHARS})'],
    "district": [rf'(?:District|जिल्हा)\s*[:\-\.;]\s*({NAME_CHARS})'],
    "birth_time": [rf'(?:जन्म\s*वेळ|Birth\s*Time)\s*[:\-\.;]\s*([{DIGITS}:\s]+(?:AM|PM)?)'],
    "birth_place": [rf'(?:जन्म\s*ठिकाण|Birth\s*Place)\s*[:\-\.;]\s*({NAME_CHARS})'],
    "caste": [rf'(?:जात|Caste)\s*[:\-\.;]\s*({NAME_CHARS})'],
    "gotra": [rf'(?:गोत्र|Gotra)\s*[:\-\.;]\s*({NAME_CHARS})'],
    "height": [rf'(?:उंची|Height)\s*[:\-\.;]\s*([{LATIN}{DEVA}{DIGITS}\s\.]+)'],
    "occupation": [rf'(?:व्यवसाय|Occupation)\s*[:\-\.;]\s*({NAME_CHARS})'],
    "father_name": [rf'(?:वडिलांचे\s*नाव|Father(?:\'s)?\s*Name)\s*[:\-\.;]\s*({NAME_CHARS})'],
    "mother_name": [rf'(?:आईचे\s*नाव|आईचं\s*नाव|Mother(?:\'s)?\s*Name)\s*[:\-\.;]\s*({NAME_CHARS})'],
    "brother": [rf'(?:भाऊ|Brother)\s*[:\-\.;]\s*({NAME_CHARS})'],
    "sister": [rf'(?:बहीण|Sister)\s*[:\-\.;]\s*({NAME_CHARS})'],
    "father_occupation": [rf'(?:वडिलांचा\s*व्यवसाय|वडिलांचा)\s*[:\-\.;]\s*([{LATIN}{DEVA}\s]+)'],
    "address": [rf'(?:पत्ता|Address)\s*[:\-\.;]\s*([{LATIN}{DEVA}\d,\s/\-]{{5,}})'],
}


def _upscale(img: np.ndarray, factor: int = 2) -> np.ndarray:
    h, w = img.shape[:2]
    return cv2.resize(img, (w * factor, h * factor), interpolation=cv2.INTER_CUBIC)


def preprocess_advanced(img: np.ndarray, scale: int = 2) -> tuple[np.ndarray, np.ndarray]:
    if scale > 1:
        img = _upscale(img, scale)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    contrast = clahe.apply(denoised)
    sharp_kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    sharpened = cv2.filter2D(contrast, -1, sharp_kernel)
    _, otsu = cv2.threshold(sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    adaptive = cv2.adaptiveThreshold(sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY, 15, 8)
    kernel = np.ones((2, 2), np.uint8)
    otsu_closed = cv2.morphologyEx(otsu, cv2.MORPH_CLOSE, kernel)
    adaptive_closed = cv2.morphologyEx(adaptive, cv2.MORPH_CLOSE, kernel)
    return otsu_closed, adaptive_closed


def _run_ocr_single(img: np.ndarray, psm: int, lang: str = "eng+mar") -> str:
    cfg = rf"--oem 3 --psm {psm}"
    try:
        return pytesseract.image_to_string(img, lang=lang, config=cfg)
    except Exception:
        return ""


def run_ocr(img: np.ndarray, lang: str = "eng+mar") -> str:
    best = ""
    for psm in (6, 3, 4):
        result = _run_ocr_single(img, psm, lang)
        if len(result.strip()) > len(best.strip()):
            best = result
    return best


def ocr_best_of_two(otsu: np.ndarray, adaptive: np.ndarray, lang: str = "eng+mar") -> str:
    t1 = run_ocr(otsu, lang)
    t2 = run_ocr(adaptive, lang)
    return t1 if len(t1.strip()) >= len(t2.strip()) else t2


# ── LANGUAGE AUTO-DETECT (Week 2, Day 1 — Sakshi) ─────────────────────────────
DEVANAGARI_RE = re.compile(rf'[{DEVA}]')

def detect_script(img: np.ndarray) -> str:
    """Cheap first-pass OCR to sample script. Returns 'latin' or 'devanagari'."""
    sample_text = _run_ocr_single(img, psm=3, lang="eng+mar")
    if DEVANAGARI_RE.search(sample_text):
        return "devanagari"
    return "latin"


def pick_lang_pack(script: str) -> str:
    """
    Map detected script → Tesseract lang string for the real OCR pass.
    NOTE: PATTERNS only has Marathi labels wired in right now, so devanagari
    still routes to 'eng+mar'. Once hi.json is wired into PATTERNS
    (Week 2 Day 2), branch this to 'eng+hin' for Hindi-specific docs.
    """
    if script == "devanagari":
        return "eng+mar"  # TODO(Day 2): branch to eng+hin once hi.json wired in
    return "eng"


def extract_table_data(img: np.ndarray, lang: str = "eng+mar") -> list[str]:
    data = pytesseract.image_to_data(
        img, output_type=pytesseract.Output.DICT,
        config=r"--oem 3 --psm 6", lang=lang,
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
    LAND_KEYS = {
        "गट क्रमांक": "plot_number", "खाते क्रमांक": "account_number",
        "सर्वेक्षण": "survey_number", "गाव": "village", "तालुका": "taluka",
        "जिल्हा": "district", "क्षेत्र": "area", "खातेदार": "owner_name",
        "survey": "survey_number", "plot": "plot_number",
        "village": "village", "district": "district",
    }
    result: dict = {}
    for label, value in kv_pairs:
        for key_fragment, field_name in LAND_KEYS.items():
            if key_fragment.lower() in label.lower():
                result[field_name] = value
                break
    return result


def extract_fields(file_path: str) -> dict:
    if file_path.lower().endswith(".pdf"):
        pages = convert_from_path(file_path, dpi=250)
        full_text, all_rows = "", []
        for page in pages:
            img_rgb = np.array(page)
            img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)

            script = detect_script(img_bgr)
            lang = pick_lang_pack(script)

            otsu, adaptive = preprocess_advanced(img_bgr, scale=1)
            full_text += "\n" + ocr_best_of_two(otsu, adaptive, lang=lang)
            all_rows.extend(extract_table_data(otsu, lang=lang))
        text = full_text
        table_data = all_rows
    else:
        img = cv2.imread(file_path)
        if img is None:
            raise ValueError(f"Cannot read file: {file_path}")

        script = detect_script(img)
        lang = pick_lang_pack(script)

        otsu, adaptive = preprocess_advanced(img, scale=2)
        text = ocr_best_of_two(otsu, adaptive, lang=lang)
        table_data = extract_table_data(otsu, lang=lang)

    print("\n🔍 OCR TEXT:\n", text)

    extracted: dict[str, str | None] = {}
    for field, patterns in PATTERNS.items():
        extracted[field] = None
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE | re.UNICODE | re.MULTILINE)
            if m:
                extracted[field] = m.group(1).strip()
                break

    if extracted.get("address") and len(extracted["address"].split()) < 2:
        extracted["address"] = None

    name = extracted.get("name")
    if not is_valid_name(name):
        name = None

    aadhaar_raw = extracted.get("aadhaar")
    aadhaar_digits: str | None = None
    aadhaar_display: str | None = None
    if aadhaar_raw:
        aadhaar_digits = re.sub(r"\D", "", aadhaar_raw)[:12]
        if len(aadhaar_digits) >= 4:
            aadhaar_display = f"XXXX-XXXX-{aadhaar_digits[-4:]}"

    kv_pairs = extract_kv_pairs(text)
    land_table = extract_land_table(kv_pairs)
    land_id = extracted.get("land_id") or land_table.get("plot_number") or \
              land_table.get("survey_number") or land_table.get("account_number")

    FAMILY_KEYS = {"वडिलांचे", "आईचे", "आईचं", "भाऊ", "बहीण",
                   "brother", "sister", "father", "mother"}
    if name is None:
        for label, value in kv_pairs:
            label_lower = label.lower()
            if "नाव" in label or "name" in label_lower:
                label_stripped = label.strip()
                first_char = label_stripped[0] if label_stripped else ""
                is_deva_start = "\u0900" <= first_char <= "\u097F"
                is_plain_latin = re.fullmatch(r"[A-Za-z]+", label_stripped) is not None
                if not (is_deva_start or is_plain_latin):
                    continue
                if not any(fk in label for fk in FAMILY_KEYS):
                    if is_valid_name(value):
                        name = value
                        break

    if name is None:
        from collections import Counter
        family_values: list[str] = [
            v for v in [
                extracted.get("father_name"), extracted.get("mother_name"),
                extracted.get("brother"), extracted.get("sister"),
            ] if v
        ]
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

    additional = {k: v for k, v in extracted.items() if k not in ("name", "land_id", "aadhaar") and v}
    if extracted.get("inferred_surname"):
        additional["inferred_surname"] = extracted["inferred_surname"]

    result: dict = {
        "name": {"value": name, "confidence": compute_confidence("name", name, text)},
        "land_id": {"value": land_id, "confidence": compute_confidence("land_id", land_id, text)},
        "aadhaar": {"value": aadhaar_display, "confidence": compute_confidence("aadhaar", aadhaar_digits, text)},
        "additional_fields": additional,
        "kv_pairs": kv_pairs,
        "land_table": land_table,
        "table_data": table_data,
    }

    if name:
        best_match, score = find_best_match(name)
        result["name"]["matched_with"] = best_match
        result["name"]["db_match"] = score
        result["name"]["flagged"] = score < 75

    required_fields = ("name", "land_id", "aadhaar")
    missing = any(result[f]["value"] is None for f in required_fields)
    valid_fs = [result[f] for f in required_fields if result[f]["value"]]
    flagged = result["name"].get("flagged", False)

    if not missing and not flagged and all(v["confidence"] >= 75 for v in valid_fs):
        result["status"] = "AUTO-VERIFIED"
    else:
        result["status"] = "REVIEW REQUIRED"

    return result


def is_valid_name(name: str | None) -> bool:
    if not name:
        return False
    if re.fullmatch(rf'(?:Name|नाव)\s*', name, re.IGNORECASE | re.UNICODE):
        return False
    if not re.search(rf'[{LATIN}{DEVA}]', name, re.UNICODE):
        return False
    if len(name.split()) < 2:
        return False
    return True


if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    IMAGE_DIR = os.path.join(BASE_DIR, "..")

    print("\nAvailable test images:")
    print("clean.jpg, partial.jpg, degraded.jpg, variation.jpg, fraud.jpg, "
          "sample.pdf, marathi.pdf, Form_1-MR.pdf, marathi_image.jpeg\n")

    img_name = input("Enter image/pdf name: ").strip()
    image_path = os.path.join(IMAGE_DIR, img_name)

    output = extract_fields(image_path)

    print("\n✅ RESULT:")
    import json
    display = {k: v for k, v in output.items() if k != "table_data"}
    print(json.dumps(display, ensure_ascii=False, indent=2))
    print(f"\n  table_data: [{len(output['table_data'])} rows]")