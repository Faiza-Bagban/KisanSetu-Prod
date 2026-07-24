# -----------------------------
# Cross Module Integration
# Crop Risk + Grievance
# -----------------------------

HIGH_RISK_DISTRICTS = [
    "nashik",
    "aurangabad",
    "solapur",
    "amravati"
]


def get_suggested_action(district: str, category: str):

    district_lower = district.lower()
    category_lower = category.lower()

    # Officer misconduct
    if category_lower == "officer misconduct":
        return "Escalate to District Vigilance Officer"

    # Drought
    if category_lower == "drought risk":
        return (
            "Initiate drought relief assessment and "
            "irrigation support"
        )

    # Flood
    if category_lower == "flood damage":
        return (
            "Activate flood compensation and crop "
            "damage relief process"
        )

    # Crop Disease
    if category_lower == "crop disease":
        return (
            "Dispatch agricultural disease inspection team"
        )

    # Irrigation
    if category_lower == "irrigation issue":
        return (
            "Escalate issue to irrigation department"
        )

    # High-risk district recommendation
    if district_lower in HIGH_RISK_DISTRICTS:
        return "Apply for PMFBY crop insurance grievance"

    return "No special recommendation"