# tests/test_auth_routes.py
# Week 5 Day 2 (Sakshi) — integration tests for auth + dashboard routes
# Uses FastAPI TestClient — no live server needed.

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# ── Helpers ───────────────────────────────────────────────────────────────────
def get_token(email="admin@kisansetu.gov", password="password123"):
    r = client.post("/auth/login", json={"email": email, "password": password})
    return r.json().get("access_token")

# ── Auth route tests ──────────────────────────────────────────────────────────

def test_login_success():
    r = client.post("/auth/login", json={"email": "admin@kisansetu.gov", "password": "password123"})
    assert r.status_code == 200
    assert "access_token" in r.json()
    assert "refresh_token" in r.json()

def test_login_wrong_password():
    r = client.post("/auth/login", json={"email": "admin@kisansetu.gov", "password": "wrongpass"})
    assert r.status_code == 401

def test_login_unknown_user():
    r = client.post("/auth/login", json={"email": "nobody@fake.com", "password": "pass"})
    assert r.status_code == 401

def test_refresh_token():
    r = client.post("/auth/login", json={"email": "admin@kisansetu.gov", "password": "password123"})
    refresh_token = r.json()["refresh_token"]
    r2 = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert r2.status_code == 200
    assert "access_token" in r2.json()

# ── Dashboard route tests ─────────────────────────────────────────────────────

# Change 403 → 401 for unauthenticated checks:
def test_admin_dashboard_requires_auth():
    r = client.get("/admin/admin-dashboard")
    assert r.status_code == 401  # not 403

def test_ndvi_summary_requires_auth():
    r = client.get("/api/ndvi-summary")
    assert r.status_code == 401  # not 403

def test_admin_dashboard_with_auth():
    token = get_token()
    r = client.get("/admin/admin-dashboard", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200

def test_ndvi_summary_with_auth():
    token = get_token()  # may hit rate limit — skip if 429
    if not token:
        pytest.skip("Rate limit hit")
    r = client.get("/api/ndvi-summary", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert "districts" in data

def test_audit_logs_admin_only():
    r = client.post("/auth/login", json={"email": "farmer1@kisansetu.gov", "password": "password123"})
    if r.status_code == 429:
        pytest.skip("Rate limit hit")
    token = r.json().get("access_token")
    r2 = client.get("/admin/api/audit-logs", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code in (401, 403)  # either is correct — no token or wrong role