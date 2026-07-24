"""
translation.py
Real bilingual translation (Marathi<->English, Hindi<->English) using
MarianMT models. Used by the RAG chatbot for multilingual query handling —
no hardcoded keyword shortcuts, genuine neural translation both directions.
"""
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

_models = {}


def _load_model(model_name):
    if model_name not in _models:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        _models[model_name] = (tokenizer, model)
    return _models[model_name]


def is_marathi(text: str) -> bool:
    return any('\u0900' <= c <= '\u097F' for c in text) and _looks_marathi_not_hindi(text)


def is_hindi(text: str) -> bool:
    return any('\u0900' <= c <= '\u097F' for c in text)


def _looks_marathi_not_hindi(text: str) -> bool:
    # Both scripts overlap heavily (Devanagari) — true language ID between
    # Hindi/Marathi from text alone is nontrivial. For now, default to Hindi
    # unless clearly Marathi-specific characters/words are present, since
    # Hindi is more common; refine with a proper language-ID model later.
    marathi_markers = ["आहे", "आहेत", "मराठी", "करा", "झाले"]
    return any(marker in text for marker in marathi_markers)


def detect_language(text: str) -> str:
    """Returns 'hi', 'mr', or 'en'."""
    if not any('\u0900' <= c <= '\u097F' for c in text):
        return "en"
    if is_marathi(text):
        return "mr"
    return "hi"


def translate_to_english(text: str, source_lang: str) -> str:
    if source_lang == "en":
        return text

    model_map = {
        "mr": "Helsinki-NLP/opus-mt-mr-en",
        "hi": "Helsinki-NLP/opus-mt-hi-en",
    }
    model_name = model_map.get(source_lang)
    if not model_name:
        return text

    tokenizer, model = _load_model(model_name)
    inputs = tokenizer(text, return_tensors="pt", padding=True)
    tokens = model.generate(**inputs)
    return tokenizer.decode(tokens[0], skip_special_tokens=True)


def translate_from_english(text: str, target_lang: str) -> str:
    if target_lang == "en":
        return text

    model_map = {
        "mr": "Helsinki-NLP/opus-mt-en-mr",
        "hi": "Helsinki-NLP/opus-mt-en-hi",
    }
    model_name = model_map.get(target_lang)
    if not model_name:
        return text

    tokenizer, model = _load_model(model_name)
    inputs = tokenizer(text, return_tensors="pt", padding=True)
    tokens = model.generate(**inputs)
    return tokenizer.decode(tokens[0], skip_special_tokens=True)


if __name__ == "__main__":
    test_hi = "मुझे फसल बीमा के बारे में जानकारी चाहिए"
    lang = detect_language(test_hi)
    en = translate_to_english(test_hi, lang)
    print(f"Detected: {lang}")
    print(f"Translated to English: {en}")

    back = translate_from_english(en, lang)
    print(f"Translated back: {back}")