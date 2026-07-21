#backend/routes/eligibility_route.py
import json, os
from fastapi import APIRouter, Depends, HTTPException
from auth.role_checker import RoleChecker
from pydantic import BaseModel, Field
from typing import List
from modules.eligibility import match_schemes

router = APIRouter()
allow_authenticated = RoleChecker(["admin", "farmer", "field_officer", "district_officer"])

# --- Paths ---
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "district_risks.json")

# --- Schemas ---
class EligibilityRequest(BaseModel):
    land_size: float = Field(..., gt=0)
    income: float = Field(..., gt=0)
    crop_type: str 
    district: str

@router.post("/api/eligibility", dependencies=[Depends(allow_authenticated)])
def check_farmer_eligibility(req: EligibilityRequest):
    """
    Futuristic Eligibility Engine:
    Combines Real-time Scheme Matching with Precomputed District Risk context.
    """
    try:
        # 1. Get ML Scheme Matches
        matches = match_schemes(req.land_size, req.income, req.crop_type, req.district)
        
        # 2. Attach District Risk Context (from the precomputed JSON)
        risk_context = None
        if os.path.exists(DATA_PATH):
            with open(DATA_PATH, "r") as f:
                data = json.load(f)
                risk_context = next((d for d in data["districts"] if d["district"] == req.district), None)

        return {
            "status": "success",
            "eligibility_results": matches,
            "district_intelligence": risk_context
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Integration Error: {str(e)}")