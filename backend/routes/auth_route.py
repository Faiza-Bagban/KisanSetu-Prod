# from fastapi import APIRouter, HTTPException
# from pydantic import BaseModel
# from auth.jwt_handler import create_access_token

# router = APIRouter()

# class LoginRequest(BaseModel):
#     email: str
#     password: str

# USERS_DB = {
#     "farmer@kisansetu.gov":           {"password": "1234", "role": "Farmer",           "name": "Ramesh Patil",  "district": "Nashik"},
#     "nashik.officer@kisansetu.gov":   {"password": "1234", "role": "Field Officer",    "name": "S. Kulkarni",   "district": "Nashik"},
#     "district.officer@kisansetu.gov": {"password": "1234", "role": "District Officer", "name": "A. Deshmukh",   "district": "All"},
#     "admin@kisansetu.gov":            {"password": "1234", "role": "Admin",            "name": "Super Admin",   "district": "All"},
# }

# def normalize_role(role: str) -> str:
#     """ ✅ Standardize role for backend RBAC logic """
#     return role.lower().replace(" ", "_")

# @router.post("/login")
# def login(req: LoginRequest):
#     user = USERS_DB.get(req.email)

#     if not user or user["password"] != req.password:
#         raise HTTPException(status_code=401, detail="Invalid credentials")

#     normalized_role = normalize_role(user["role"])

#     # ✅ FIX: Include district in the JWT payload for Audit Logging
#     token = create_access_token({
#         "sub": req.email,
#         "role": normalized_role,
#         "district": user["district"]  # Now available for idp_route.py
#     })

#     return {
#         "access_token": token,
#         "user": {
#             "email":    req.email,
#             "name":     user["name"],
#             "district": user["district"],
#             "role":     user["role"] # Original format for frontend UI
#         }
#     }

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models.user_model import User

from auth.jwt_handler import create_access_token
from auth.pwd_utils import verify_password

router = APIRouter()


class LoginRequest(BaseModel):
    email: str
    password: str


def normalize_role(role: str) -> str:
    return role.lower().replace(" ", "_")


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):

    # ✅ REAL DATABASE USER QUERY
    user = db.query(User).filter(User.username == req.email).first()
    print("LOGIN EMAIL:", req.email)
    print("DB USER:", user)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # ✅ PASSWORD HASH VERIFY
    if not verify_password(req.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    normalized_role = normalize_role(user.role)

    token = create_access_token({
        "sub": user.username,
        "role": normalized_role,
        "district": user.district
    })

    return {
        "access_token": token,
        "user": {
            "email": user.username,
            "name": user.username.split("@")[0],
            "district": user.district,
            "role": user.role.replace("_", " ").title()
        }
    }