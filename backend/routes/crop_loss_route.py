#backend/routes/crop_loss_route.py
import os
import pandas as pd
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

@router.get("/api/ndvi-summary", dependencies=[Depends(allow_authenticated)])
def get_ndvi_summary():
    """
    Returns latest NDVI drop + rainfall deficit per district from
    the real merged crop-loss dataset (backend/data/processed/crop_loss_merged.csv).
    Used by frontend AdminMap to replace random NDVI values with real data.
    """
    csv_path = os.path.join(
        os.path.dirname(__file__), "..", "data", "processed", "crop_loss_merged.csv"
    )
    try:
        df = pd.read_csv(csv_path)
        # Get latest row per district
        df["date"] = pd.to_datetime(df["date"])
        latest = df.sort_values("date").groupby("district").last().reset_index()
        result = []
        for _, row in latest.iterrows():
            result.append({
                "district": row["district"],
                "ndvi_drop": round(float(row.get("ndvi_drop", 0)), 3),
                "rainfall_deficit": round(float(row.get("rainfall_deficit", 0)), 1),
                "temp_anomaly": round(float(row.get("temp_anomaly", 0)), 2),
                "soil_moisture": round(float(row.get("soil_moisture", 0)), 3) if row.get("soil_moisture") else None,
                "date": str(row["date"].date()),
            })
        return {"districts": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CSV read error: {str(e)}")