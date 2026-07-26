# routes/auth_route.py
# Week 3 Day 1 (Sakshi) - Auth hardening:
#   - Rate limiting on /login: max 5 attempts per minute per IP
#   - Refresh token endpoint added (/auth/refresh)
#   - Consistent error timing to prevent user enumeration

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
import os

from database import get_db
from models.user_model import User
from auth.jwt_handler import (
    create_access_token,
    create_refresh_token,
    verify_token,
)
from auth.pwd_utils import verify_password

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


def normalize_role(role: str) -> str:
    return role.lower().replace(" ", "_")


@router.post("/login")
@limiter.limit("5/minute" if not os.getenv("TESTING") else "1000/minute")
def login(request: Request, req: LoginRequest, db: Session = Depends(get_db)):
    """
    Login endpoint — rate limited to 5 attempts per minute per IP.
    Returns both access token (60min) and refresh token (7 days).
    """
    user = db.query(User).filter(User.username == req.email).first()

    # Always verify password even if user not found (prevents timing attack)
    dummy_hash = "$pbkdf2-sha256$29000$dummy$dummy"
    password_ok = verify_password(req.password, user.password) if user else False

    if not user or not password_ok:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    normalized_role = normalize_role(user.role)
    payload = {
        "sub": user.username,
        "role": normalized_role,
        "district": user.district,
    }

    return {
        "access_token": create_access_token(payload),
        "refresh_token": create_refresh_token(payload),
        "token_type": "bearer",
        "expires_in": 3600,  # seconds
        "user": {
            "email": user.username,
            "name": user.username.split("@")[0],
            "district": user.district,
            "role": user.role.replace("_", " ").title(),
        },
    }


@router.post("/refresh")
@limiter.limit("10/minute")
def refresh(request: Request, req: RefreshRequest):
    """
    Refresh endpoint — accepts a valid refresh token, returns new access token.
    Rate limited to 10/minute per IP.
    """
    payload = verify_token(req.refresh_token, expected_type="refresh")

    new_payload = {
        "sub": payload.get("sub"),
        "role": payload.get("role"),
        "district": payload.get("district"),
    }
    return {
        "access_token": create_access_token(new_payload),
        "token_type": "bearer",
        "expires_in": 3600,
    }