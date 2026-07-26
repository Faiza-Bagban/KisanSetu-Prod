"""
LLM-based eligibility reasoning — replaces hardcoded numeric threshold
matching with actual reasoning over real scheme criteria text.
"""
import ollama
import json
from data.schemes_real import REAL_SCHEMES

MODEL = "llama3.1:8b"


def check_scheme_eligibility(farmer_profile: dict, scheme: dict) -> dict:
    """
    Uses local LLM to reason about whether a farmer is eligible for one
    scheme, given the scheme's real criteria text.
    """
    prompt = f"""You are an eligibility checker for Indian government farmer schemes.
Given a farmer's profile and a scheme's real eligibility criteria, determine eligibility.

FARMER PROFILE:
- Land size: {farmer_profile.get('land_size')} acres
- Annual income: ₹{farmer_profile.get('income')}
- Crop type: {farmer_profile.get('crop_type')}
- District: {farmer_profile.get('district')}
- Government employee: {farmer_profile.get('is_govt_employee', 'unknown')}
- Pays income tax: {farmer_profile.get('pays_income_tax', 'unknown')}

SCHEME: {scheme['name']} ({scheme['id']})
CRITERIA:
{scheme['criteria']}

Respond ONLY with valid JSON in this exact format, no other text:
{{
  "eligible": true or false or "needs_more_info",
  "confidence": 0-100,
  "reasoning": "short explanation",
  "missing_info": ["list of profile fields needed to be certain, if any"]
}}
"""

    # response = ollama.chat(model=MODEL, messages=[
    #     {"role": "user", "content": prompt}
    # ])
    # response = ollama.chat(model=MODEL, messages=[
    #     {"role": "user", "content": prompt}
    # ], options={"temperature": 0})

    # content = response["message"]["content"].strip()

    try:
        response = ollama.chat(model=MODEL, messages=[
            {"role": "user", "content": prompt}
        ], options={"temperature": 0})
        content = response["message"]["content"].strip()
    except Exception:
        return {
            "eligible": "needs_more_info",
            "confidence": 0,
            "reasoning": "AI reasoning temporarily unavailable — please try again shortly or contact your District Agriculture Office.",
            "missing_info": [],
            "scheme": scheme["id"],
            "scheme_name": scheme["name"],
            "documents_required": scheme["documents"],
            "service_status": "degraded",
        }

    # Strip markdown code fences if the model wraps JSON in ```json blocks
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]

    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        result = {
            "eligible": "needs_more_info",
            "confidence": 0,
            "reasoning": "Could not parse model response",
            "missing_info": [],
            "raw_response": content,
        }

    result["scheme"] = scheme["id"]
    result["scheme_name"] = scheme["name"]
    result["documents_required"] = scheme["documents"]
    return result


def match_schemes_ai(farmer_profile: dict) -> dict:
    """Checks farmer eligibility against all real schemes using LLM reasoning."""
    results = []
    for scheme in REAL_SCHEMES:
        result = check_scheme_eligibility(farmer_profile, scheme)
        results.append(result)

    eligible = [r for r in results if r["eligible"] is True]
    needs_info = [r for r in results if r["eligible"] == "needs_more_info"]

    return {
        "eligible_schemes": eligible,
        "needs_more_info": needs_info,
        "all_results": results,
    }


if __name__ == "__main__":
    test_profile = {
        "land_size": 2,
        "income": 150000,
        "crop_type": "wheat",
        "district": "Pune",
        "is_govt_employee": False,
        "pays_income_tax": False,
    }
    result = match_schemes_ai(test_profile)
    print(json.dumps(result, indent=2))