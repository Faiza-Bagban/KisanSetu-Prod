# -----------------------------
# Grievance Priority Scoring
# -----------------------------

# -----------------------------
# Grievance Priority Scoring
# -----------------------------

URGENT_KEYWORDS = [
    "bribe",
    "fraud",
    "corruption",
    "harassment",
    "urgent",
    "emergency",
    "drought",
    "no rainfall",
    "drying",
    "crop damage",
    "water shortage",
    "flood",
    "heatwave",
    "farmer suicide",
    "रिश्वत",       # bribe (Hindi)
    "भ्रष्टाचार",    # corruption (Hindi — same word as Marathi actually)

    "लाच",
    "भ्रष्टाचार",
]

HIGH_KEYWORDS = [
    "delay",
    "pending",
    "not received",
    "rejected",
    "problem",
    "complaint",
    "disease",
    "irrigation",

    "विलंब",
    "प्रलंबित",
    "तक्रार",
    "देरी",         # delay (Hindi)
    "लंबित",        # pending (Hindi)
    "शिकायत",       # complaint (Hindi)
]


def calculate_priority(text: str):

    text_lower = text.lower()

    for word in URGENT_KEYWORDS:
        if word in text_lower:
            return "HIGH"

    for word in HIGH_KEYWORDS:
        if word in text_lower:
            return "MEDIUM"

    return "NORMAL"