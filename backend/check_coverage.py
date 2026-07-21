import json
from modules.eligibility import SCHEMES

with open("data/demo_results.json") as f:
    data = json.load(f)

covered = set()

for farmer in data:
    for s in farmer["schemes"]:
        covered.add(s["scheme"])

all_schemes = set([s["id"] for s in SCHEMES])

missing = all_schemes - covered

print("✅ Covered Schemes:", covered)
print("🔢 Total Covered:", len(covered))

if len(missing) == 0:
    print("🎉 All schemes are covered!")
else:
    print("❌ Missing schemes:", missing)