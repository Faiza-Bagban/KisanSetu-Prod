from modules.eligibility_ai import check_scheme_eligibility, match_schemes_ai
from data.schemes_real import REAL_SCHEMES


def _get_scheme(scheme_id):
    return next(s for s in REAL_SCHEMES if s["id"] == scheme_id)


# ✅ Test 1: Small farmer should be eligible for PM-KISAN (no land/income cap in real scheme)
def test_small_farmer_pmkisan():
    profile = {
        "land_size": 0.1,
        "income": 50000,
        "crop_type": "rice",
        "district": "Pune",
        "is_govt_employee": False,
        "pays_income_tax": False,
    }
    result = check_scheme_eligibility(profile, _get_scheme("PM-KISAN"))

    assert result["eligible"] in (True, "needs_more_info")
    assert "confidence" in result
    assert 0 <= result["confidence"] <= 100


# ✅ Test 2: Government employee should typically be excluded from PM-KISAN
def test_govt_employee_pmkisan_excluded():
    profile = {
        "land_size": 2,
        "income": 300000,
        "crop_type": "wheat",
        "district": "Nashik",
        "is_govt_employee": True,
        "pays_income_tax": True,
    }
    result = check_scheme_eligibility(profile, _get_scheme("PM-KISAN"))

    # Real PM-KISAN excludes govt employees and income-tax payers —
    # model should reason toward false or needs_more_info, not confidently true
    assert result["eligible"] in (False, "needs_more_info")


# ✅ Test 3: PMFBY has no income cap — high income should not disqualify
def test_high_income_pmfby_not_disqualified():
    profile = {
        "land_size": 5,
        "income": 800000,
        "crop_type": "cotton",
        "district": "Aurangabad",
        "is_govt_employee": False,
        "pays_income_tax": False,
    }
    result = check_scheme_eligibility(profile, _get_scheme("PMFBY"))

    assert result["eligible"] in (True, "needs_more_info")


# ✅ Test 4: Cluster-based schemes (PKVY) should never claim confident individual eligibility
def test_pkvy_flags_cluster_requirement():
    profile = {
        "land_size": 3,
        "income": 150000,
        "crop_type": "wheat",
        "district": "Pune",
        "is_govt_employee": False,
        "pays_income_tax": False,
    }
    result = check_scheme_eligibility(profile, _get_scheme("PKVY"))

    # Should not confidently say "true" without cluster info — either
    # needs_more_info or false, since individual application isn't possible
    assert result["eligible"] != True or result["confidence"] < 70


# ✅ Test 5: Full match_schemes_ai returns all real schemes, well-formed output
def test_match_schemes_ai_full_run():
    profile = {
        "land_size": 2,
        "income": 150000,
        "crop_type": "wheat",
        "district": "Pune",
        "is_govt_employee": False,
        "pays_income_tax": False,
    }
    result = match_schemes_ai(profile)

    assert "eligible_schemes" in result
    assert "needs_more_info" in result
    assert "all_results" in result
    assert len(result["all_results"]) == len(REAL_SCHEMES)