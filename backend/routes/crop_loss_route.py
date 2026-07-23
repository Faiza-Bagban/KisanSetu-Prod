#backend/routes/crop_loss_route.py
from fastapi import APIRouter, Depends, HTTPException
from auth.role_checker import RoleChecker
from pydantic import BaseModel, Field
from modules.crop_loss import predict_risk

router = APIRouter()
allow_authenticated = RoleChecker(["admin", "farmer", "field_officer", "district_officer"])

# --- Schemas ---
class CropLossRequest(BaseModel):
    district: str
    rainfall_deficit: float
    temp_anomaly: float
    ndvi_drop: float = Field(..., ge=0)
    soil_moisture: float
    days_since_rain: int = Field(..., ge=0)

@router.post("/api/crop-loss", dependencies=[Depends(allow_authenticated)])
def check_crop_loss_risk(req: CropLossRequest):
    """
    Crop Loss Risk Prediction:
    Predicts drought/loss risk for a district based on real IMD rainfall/temp,
    NDVI, and soil moisture features. Trained on real 2024 data (currently
    Pune only) — model will reject unknown districts until more district
    data is collected and retrained.
    """
    try:
        result = predict_risk(
            district=req.district,
            rainfall_deficit=req.rainfall_deficit,
            temp_anomaly=req.temp_anomaly,
            ndvi_drop=req.ndvi_drop,
            soil_moisture=req.soil_moisture,
            days_since_rain=req.days_since_rain,
        )

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return {
            "status": "success",
            "prediction": result,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Integration Error: {str(e)}")