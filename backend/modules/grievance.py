#backend/modules/grievance.py
import random

from transformers import (
    pipeline,
    AutoTokenizer,
    AutoModelForSeq2SeqLM
)


# experimental merging part with imports from that folder
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from experimental.grievance_priority import calculate_priority
from experimental.grievance_crossmodule import get_suggested_action
from experimental.grievance_deduplication import check_duplicate
from experimental.grievance_resolution_model import predict_resolution_ml


# -----------------------------
# Lazy-Loaded Models (Marathi translator + zero-shot classifier)
# Only load into memory when actually first used — reduces startup
# memory footprint significantly (needed for constrained hosting).
# -----------------------------

translator_model_name = "Helsinki-NLP/opus-mt-mr-en"
_translator_tokenizer = None
_translator_model = None
_classifier = None


def get_translator():
    global _translator_tokenizer, _translator_model
    if _translator_model is None:
        _translator_tokenizer = AutoTokenizer.from_pretrained(translator_model_name)
        _translator_model = AutoModelForSeq2SeqLM.from_pretrained(translator_model_name)
    return _translator_tokenizer, _translator_model


def get_classifier():
    global _classifier
    if _classifier is None:
        _classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli"
        )
    return _classifier


# -----------------------------
# Categories
# -----------------------------

CATEGORIES = [
    "scheme delay",
    "document rejection",
    "payment issue",
    "officer misconduct",
    "drought risk",
    "flood damage",
    "crop disease",
    "irrigation issue",
    "other"
]

# -----------------------------
# Base Resolution Days
# -----------------------------

RESOLUTION_DAYS = {
    "scheme delay": "5-7 working days",
    "document rejection": "2-3 working days",
    "payment issue": "7-10 working days",
    "officer misconduct": "10-15 working days",

    "drought risk": "1-2 working days",
    "flood damage": "1-3 working days",
    "crop disease": "2-4 working days",
    "irrigation issue": "3-5 working days",

    "other": "5-7 working days",
}

# -----------------------------
# Dynamic Severity Logic
# -----------------------------

SEVERITY_KEYWORDS = {
    "urgent": 3,
    "months": 2,
    "month": 2,
    "pending": 2,
    "delay": 2,
    "not received": 2,
    "rejected": 1,
    "harassment": 4,
    "corruption": 5,
    "bribe": 5,
    "fraud": 5,
    "officer": 2,
    "complaint": 1,
    "problem": 1,
    "rainfall": 4,
    "drought": 5,
    "drying": 4,
    "water shortage": 5,
    "crop damage": 5,
    "flood": 5,
    "disease": 4,
    "heatwave": 5,
    "irrigation": 3,
}

# -----------------------------
# Marathi Keyword Mapping
# -----------------------------

MARATHI_HINTS = {
    # Payment Issues
    "पैसे": "payment issue",
    "विमा": "payment issue",
    "पेमेंट": "payment issue",
    "अनुदान": "payment issue",
    "रक्कम": "payment issue",
    "मिळाले नाही": "payment issue",
    "मिळाले नाहीत": "payment issue",
    "सब्सिडी": "payment issue",
    "पीक विमा": "payment issue",
    "शेतकरी योजना पैसे": "payment issue",

    # Document Rejection
    "कागद": "document rejection",
    "दस्तऐवज": "document rejection",
    "कागदपत्र": "document rejection",
    "रिजेक्ट": "document rejection",
    "नाकारले": "document rejection",
    "अपूर्ण": "document rejection",
    "दाखला": "document rejection",

    # Officer Misconduct
    "अधिकारी": "officer misconduct",
    "लाच": "officer misconduct",
    "भ्रष्टाचार": "officer misconduct",
    "छळ": "officer misconduct",
    "धमकी": "officer misconduct",
    "वर्तन": "officer misconduct",
    "गैरवर्तन": "officer misconduct",

    # Scheme Delay
    "योजना": "scheme delay",
    "विलंब": "scheme delay",
    "प्रलंबित": "scheme delay",
    "उशीर": "scheme delay",
    "मंजूर": "scheme delay",
    "प्रक्रिया": "scheme delay",
    "अजून झाले नाही": "scheme delay",
    "बाकी": "scheme delay",

    # Generic Complaint
    "तक्रार": "other",
    "समस्या": "other",
    "अडचण": "other",
}


# -----------------------------
# New- Grievance ID Generator
# -----------------------------

def generate_grievance_id():
    random_number = random.randint(1000, 9999)
    return f"GRV-2026-{random_number}"


# -----------------------------
# Marathi Detection
# -----------------------------

def is_marathi(text: str) -> bool:
    return any('\u0900' <= c <= '\u097F' for c in text)


# -----------------------------
# Marathi Category Hint
# -----------------------------

def detect_marathi_category(text: str):
    for keyword, category in MARATHI_HINTS.items():
        if keyword in text:
            return category
    return None


# -----------------------------
# Dynamic Resolution Prediction
# -----------------------------

def predict_resolution_days(text: str, category: str) -> str:
    base_days = {
        "scheme delay": 6,
        "document rejection": 3,
        "payment issue": 8,
        "officer misconduct": 12,
        "other": 5,
    }

    days = base_days.get(category, 5)
    text_lower = text.lower()

    for keyword, extra_days in SEVERITY_KEYWORDS.items():
        if keyword in text_lower:
            days += extra_days

    return f"{days} working days"


# -----------------------------
# Main Classification Function
# -----------------------------

def classify_grievance(text: str, district: str = "Pune") -> dict:

    original_text = text
    translated_text = None
    forced_category = None

    # Marathi Handling
    if is_marathi(text):

        forced_category = detect_marathi_category(text)

        try:
            translator_tokenizer, translator_model = get_translator()
            inputs = translator_tokenizer(
                text,
                return_tensors="pt",
                padding=True
            )

            translated_tokens = translator_model.generate(**inputs)

            translated_text = translator_tokenizer.decode(
                translated_tokens[0],
                skip_special_tokens=True
            )

            # Ignore weak translation
            if translated_text and len(translated_text.split()) >= 3:
                text = translated_text

        except Exception:
            translated_text = None

    # Classification
    result = get_classifier()(text, CATEGORIES)

    predicted_category = result["labels"][0]

    # Trust the real classifier by default. Only fall back to keyword
    # hints if translation failed entirely (so classification ran on
    # untranslated Marathi text, which BART/zero-shot can't handle well).
    confidence = round(result["scores"][0] * 100, 1)

    if translated_text is None and forced_category:
        # Translation failed — keyword hint is our only real signal
        top_category = forced_category
        confidence = 60.0  # honest moderate confidence, not artificially boosted
    else:
        top_category = predicted_category

    duplicate_flag = check_duplicate(district, top_category)
    return {
        "grievance_id": generate_grievance_id(),

        "priority": calculate_priority(original_text),
        "suggested_action": get_suggested_action(district, top_category),
        "possible_duplicate": duplicate_flag,

        "original_text": original_text,
        "category": top_category,
        "confidence": confidence,
        "resolution_time": predict_resolution_ml(top_category),
        "routed_to": (
            "Disaster Management Officer"
            if top_category in ["drought risk", "flood damage"]
            else "Agriculture Disease Control Officer"
            if top_category == "crop disease"
            else "Irrigation Department Officer"
            if top_category == "irrigation issue"
            else "District Agriculture Officer"
        ),
    }


# -----------------------------
# Testing Block
# -----------------------------

if __name__ == "__main__":

    test_samples = [
        "My PM-KISAN payment has not arrived for 3 months",
        "My crop subsidy payment is still pending",
        "माझे पीक विमा पैसे अजून मिळाले नाहीत",
        "Officer asked for bribe during document verification",
        "माझे कागद कारणाशिवाय reject झाले",
        "My scheme approval is delayed for months",
        "अधिकारी योग्य माहिती देत नाही",
        "Payment not received despite approval",
        "My application is pending since last month",
        "माझी तक्रार अजून सोडवली नाही"
    ]

    for i, sample in enumerate(test_samples, 1):
        print("\n" + "=" * 60)
        print(f"Test Case {i}")
        print(f"Input: {sample}")
        print("Output:")
        print(classify_grievance(sample))