import json
from modules.eligibility import match_schemes

with open("data/demo_farmers.json") as f:
    farmers = json.load(f)

results = []

for i, farmer in enumerate(farmers):
    res = match_schemes(**farmer)
    results.append({
        "farmer_id": i + 1,
        "input": farmer,
        "schemes": res if isinstance(res, list) else []
    })

with open("data/demo_results.json", "w") as f:
    json.dump(results, f, indent=2)

print("✅ Demo results generated!")