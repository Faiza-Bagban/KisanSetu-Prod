# -----------------------------
# Duplicate Detection
# -----------------------------

existing_grievances = [
    {
        "district": "Nashik",
        "category": "payment issue"
    },
    {
        "district": "Pune",
        "category": "scheme delay"
    },
    {
        "district": "Solapur",
        "category": "payment issue"
    },
    {
        "district": "Aurangabad",
        "category": "document rejection"
    }
]


def check_duplicate(district: str, category: str):

    for grievance in existing_grievances:

        if (
            grievance["district"].lower() == district.lower()
            and grievance["category"].lower() == category.lower()
        ):
            return True

    return False