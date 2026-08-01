import json
from modules.eligibility_ai import match_schemes_ai

with open("data/demo_farmers.json") as f:
    data = json.load(f)

farmers = data["farmers"]

results = []

for farmer in farmers:
    profile = {
        "land_size": farmer.get("land"),
        "income": farmer.get("income"),
        "crop_type": farmer.get("crop"),
        "district": farmer.get("district"),
        "is_govt_employee": farmer.get("is_govt_employee", False),
        "pays_income_tax": farmer.get("pays_income_tax", False),
    }
    res = match_schemes_ai(profile)
    results.append({
        "farmer_id": farmer.get("id"),
        "name": farmer.get("name"),
        "input": profile,
        "schemes": res.get("eligible_schemes", [])
    })

with open("data/demo_results.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"Demo results regenerated with AI reasoning for {len(farmers)} farmers!")