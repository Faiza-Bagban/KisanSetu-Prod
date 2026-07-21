import re

def keyword_present(text, keyword):
    return keyword.lower() in text.lower()


def length_score(value):
    if not value:
        return 20
    if len(value) > 10:
        return 90
    return 70


def aadhaar_format_score(aadhaar):
    if not aadhaar:
        return 20

    if re.fullmatch(r"\d{12}", aadhaar):
        return 95
    return 60


def compute_confidence(field, value, text):
    base = 50

    if field == "name":
       if keyword_present(text, "Name"):
        base += 25
       if value:
        base += min(len(value.split()) * 10, 20)

    elif field == "land_id":
        if keyword_present(text, "Survey"):
            base += 20
        base += length_score(value) // 5

    elif field == "aadhaar":
        base = aadhaar_format_score(value)

    return min(base, 100)