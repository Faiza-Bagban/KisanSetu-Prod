from modules.eligibility import match_schemes

# ✅ Test 1: Invalid crop (mango)
def test_invalid_crop():
    result = match_schemes(2, 100000, "mango", "Nashik")

    assert isinstance(result, dict)
    assert result["schemes"] == []
    assert "message" in result


# ✅ Test 2: Zero income
def test_zero_income():
    result = match_schemes(2, 0, "wheat", "Nashik")

    assert isinstance(result, list)
    assert len(result) > 0

    # Check confidence is reasonable
    for scheme in result:
        assert scheme["confidence"] >= 0


# ✅ Test 3: Very small land (0.1 acre)
def test_small_land():
    result = match_schemes(0.1, 50000, "rice", "Pune")

    assert isinstance(result, list)
    assert len(result) > 0

    # Expect high eligibility
    assert result[0]["confidence"] >= 70


# ✅ Test 4: Large income (should reduce eligibility)
def test_high_income():
    result = match_schemes(2, 600000, "wheat", "Delhi")

    assert isinstance(result, list)
    # Might be empty or low confidence
    if len(result) > 0:
        assert result[0]["confidence"] < 90