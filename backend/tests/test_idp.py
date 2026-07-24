# tests/test_idp.py
# Week 5 Day 3 (Sakshi) — OCR/IDP module tests

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from modules.idp import is_valid_name, extract_kv_pairs, detect_script
import numpy as np

# ── is_valid_name tests ───────────────────────────────────────────────────────

def test_valid_english_name():
    assert is_valid_name("Ramesh Patil")

def test_valid_marathi_name():
    assert is_valid_name("मितेन मियाणी")

def test_single_word_invalid():
    assert not is_valid_name("Ramesh")

def test_none_invalid():
    assert not is_valid_name(None)

def test_empty_invalid():
    assert not is_valid_name("")

def test_label_word_invalid():
    assert not is_valid_name("Name")
    assert not is_valid_name("नाव")
    assert not is_valid_name("नाम")

def test_digits_only_invalid():
    assert not is_valid_name("1234 5678")

# ── extract_kv_pairs tests ────────────────────────────────────────────────────

def test_kv_pairs_english():
    text = "Name: Ramesh Patil\nSurvey: MH-1234"
    pairs = extract_kv_pairs(text)
    labels = [p[0] for p in pairs]
    assert "Name" in labels

def test_kv_pairs_marathi():
    text = "नाव : मितेन मियाणी\nजात : हिंदू"
    pairs = extract_kv_pairs(text)
    assert len(pairs) >= 1

def test_kv_pairs_empty_text():
    pairs = extract_kv_pairs("")
    assert pairs == []

def test_kv_pairs_no_separator():
    pairs = extract_kv_pairs("Just some plain text without colons")
    assert pairs == []

# ── detect_script tests ───────────────────────────────────────────────────────

def test_detect_script_latin():
    # White image — no Devanagari → should be latin
    img = np.ones((100, 300, 3), dtype=np.uint8) * 255
    result = detect_script(img)
    assert result == "latin"