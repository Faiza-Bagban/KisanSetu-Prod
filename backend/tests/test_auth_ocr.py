# tests/test_auth_ocr.py
# Week 5 Day 1 (Sakshi) — unit tests for auth + OCR modules

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from auth.jwt_handler import create_access_token, verify_token, create_refresh_token
from auth.pwd_utils import hash_password, verify_password
from modules.idp import is_valid_name


# ── JWT tests ─────────────────────────────────────────────────────────────────

def test_access_token_roundtrip():
    payload = {"sub": "test@kisansetu.gov", "role": "farmer", "district": "Pune"}
    token = create_access_token(payload)
    decoded = verify_token(token, expected_type="access")
    assert decoded["sub"] == "test@kisansetu.gov"
    assert decoded["role"] == "farmer"

def test_refresh_token_roundtrip():
    payload = {"sub": "test@kisansetu.gov", "role": "admin", "district": "All"}
    token = create_refresh_token(payload)
    decoded = verify_token(token, expected_type="refresh")
    assert decoded["sub"] == "test@kisansetu.gov"

def test_access_token_rejected_as_refresh():
    from fastapi import HTTPException
    payload = {"sub": "x@y.com", "role": "farmer", "district": "Pune"}
    token = create_access_token(payload)
    with pytest.raises(HTTPException):
        verify_token(token, expected_type="refresh")

def test_invalid_token_raises():
    from fastapi import HTTPException
    with pytest.raises(HTTPException):
        verify_token("not.a.real.token")


# ── Password tests ────────────────────────────────────────────────────────────

def test_password_hash_verify():
    hashed = hash_password("mypassword123")
    assert verify_password("mypassword123", hashed)

def test_wrong_password_fails():
    hashed = hash_password("correct")
    assert not verify_password("wrong", hashed)


# ── OCR / IDP unit tests ──────────────────────────────────────────────────────

def test_is_valid_name_passes():
    assert is_valid_name("Ramesh Patil")
    assert is_valid_name("मितेन मियाणी")

def test_is_valid_name_single_word_fails():
    assert not is_valid_name("Ramesh")

def test_is_valid_name_none_fails():
    assert not is_valid_name(None)

def test_is_valid_name_label_word_fails():
    assert not is_valid_name("Name")
    assert not is_valid_name("नाव")