"""
build_grievance_training_data.py
Generates a labeled training set for the lightweight grievance classifier.
NOTE: These are template-generated synthetic examples per category, not
real farmer complaints — a genuine labeled real-world dataset doesn't
exist yet. This is a heuristic/synthetic training set, same honest
caveat as crop_loss.py's heuristic risk label. Replace with real
labeled grievance data when available.
"""
import pandas as pd
import os

TEMPLATES = {
    "payment issue": [
        "My {scheme} payment has not arrived for {n} months",
        "Subsidy amount for {scheme} still pending in my account",
        "Payment for crop insurance claim not received",
        "My bank account did not receive the {scheme} installment",
        "Amount promised under {scheme} never credited",
        "PM-KISAN money not transferred this quarter",
        "Insurance payout for crop damage is delayed",
        "Subsidy for fertilizer purchase not received yet",
    ],
    "document rejection": [
        "My land document was rejected without any reason",
        "Aadhaar verification failed during scheme application",
        "Application rejected due to incomplete documents",
        "My income certificate was not accepted",
        "Bank passbook copy got rejected by the officer",
        "Land ownership proof was declared invalid",
        "My documents were returned saying they are not valid",
        "Officer said my paperwork is incomplete without explaining why",
    ],
    "officer misconduct": [
        "Officer asked for bribe to process my application",
        "Field officer was rude and refused to help",
        "Corruption at the local agriculture office",
        "Officer demanded money for document verification",
        "Local official is not cooperating and asking for favors",
        "Officer harassed me when I asked about my application status",
        "Agriculture officer threatened me for filing a complaint",
        "Bribe was demanded before my file would be processed",
    ],
    "drought risk": [
        "No rainfall in our village for over a month",
        "Severe water shortage affecting our crops",
        "Drought conditions are destroying our wheat field",
        "We need urgent drought relief assistance",
        "Our region has had no rain and crops are drying up",
        "Water levels have dropped severely this season",
        "Drought is threatening our entire harvest this year",
        "No irrigation water available due to ongoing drought",
    ],
    "flood damage": [
        "Flood destroyed our entire rice crop this season",
        "Heavy rains flooded our fields, crops are ruined",
        "Need compensation for flood damage to farmland",
        "Our farmland was submerged after the recent floods",
        "Flood water damaged our stored grain and equipment",
        "Excessive rainfall caused flooding across our fields",
        "We lost our entire sugarcane crop to flooding",
        "Flood relief is urgently needed for our village",
    ],
    "crop disease": [
        "Our cotton crop has a disease spreading rapidly",
        "Pest infestation is destroying our tomato plants",
        "Need urgent help, crop disease affecting whole field",
        "Fungal infection is spreading across our wheat crop",
        "Insects are destroying our soybean plants",
        "Our onion crop is showing signs of a serious disease",
        "Blight has affected most of our potato field",
        "Need pesticide support, pest attack on our crops",
    ],
    "irrigation issue": [
        "Irrigation canal near our farm is broken",
        "No water supply for irrigation this month",
        "Water pump for irrigation not working, need repair",
        "Irrigation channel is blocked and needs clearing",
        "Our borewell for irrigation has stopped working",
        "Drip irrigation system installed under the scheme is faulty",
        "Water distribution for irrigation is unfair in our area",
        "Irrigation infrastructure was never completed as promised",
    ],
    "scheme delay": [
        "My {scheme} approval is delayed for {n} months",
        "Application under {scheme} pending since last month",
        "Scheme registration process is taking too long",
        "Still waiting for approval under the government scheme",
        "My scheme application has not been processed in weeks",
        "No update on my application status for the scheme",
        "Approval process for the scheme is extremely slow",
        "Been waiting for scheme enrollment confirmation for a long time",
    ],
    "other": [
        "I have a general complaint about farming support",
        "Need information about available government schemes",
        "General query regarding agricultural assistance",
        "Would like to know more about farmer welfare programs",
        "Have a question about how to apply for support services",
        "Requesting general guidance on agricultural policies",
        "Need help understanding the application process",
        "General feedback about the farmer support system",
    ],
}

SCHEMES = ["PM-KISAN", "PMFBY", "KCC", "crop insurance", "the scheme"]


def generate_dataset():
    rows = []
    for category, templates in TEMPLATES.items():
        for template in templates:
            if "{scheme}" in template or "{n}" in template:
                for n in [2, 3, 4]:
                    for scheme in SCHEMES[:2]:
                        text = template.format(scheme=scheme, n=n)
                        rows.append({"text": text, "category": category})
            else:
                rows.append({"text": template, "category": category})

    df = pd.DataFrame(rows).drop_duplicates(subset="text")
    return df


if __name__ == "__main__":
    df = generate_dataset()
    out_path = os.path.join(os.path.dirname(__file__), "..", "data", "grievance_training_data.csv")
    df.to_csv(out_path, index=False)
    print(f"Generated {len(df)} labeled training examples")
    print(df["category"].value_counts())