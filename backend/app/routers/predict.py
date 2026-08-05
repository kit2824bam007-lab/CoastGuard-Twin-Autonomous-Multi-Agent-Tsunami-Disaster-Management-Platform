"""
/predict-risk — run the risk model on demand (manual testing / simulation)
and fetch stored predictions.
"""
import logging
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.orm import RiskPrediction
from app.models.schemas import ManualPredictRequest, RiskPredictionResult, RiskPredictionOut
from app.services.risk_model import get_active_risk_model

logger = logging.getLogger("tsunami.api.predict")
router = APIRouter(prefix="/predict-risk", tags=["predict"])
risk_model = get_active_risk_model()


@router.post("/", response_model=RiskPredictionResult, summary="Run risk model on manual input (used for simulation/testing)")
async def predict_risk(payload: ManualPredictRequest):
    result = risk_model.predict(
        magnitude=payload.magnitude,
        depth_km=payload.depth_km,
        latitude=payload.latitude,
        longitude=payload.longitude,
        is_offshore=payload.is_offshore,
    )
    return RiskPredictionResult(
        risk_level=result.risk_level,
        risk_score=result.risk_score,
        explanation=result.explanation,
        model_version=result.model_version,
    )


@router.get("/history", response_model=list[RiskPredictionOut], summary="Recent stored risk predictions")
async def prediction_history(limit: int = 50, db: AsyncSession = Depends(get_db)):
    stmt = select(RiskPrediction).order_by(RiskPrediction.predicted_at.desc()).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


from app.models.orm import TsunamiForecast
from app.models.schemas import TsunamiForecastOut

@router.get("/forecast/{earthquake_id}", response_model=list[TsunamiForecastOut], summary="Fetch predicted wave forecasts for an earthquake")
async def get_tsunami_forecast(earthquake_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(TsunamiForecast).where(TsunamiForecast.earthquake_id == earthquake_id).order_by(TsunamiForecast.arrival_time_hours.asc())
    result = await db.execute(stmt)
    return result.scalars().all()
