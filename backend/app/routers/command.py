"""Paper-aligned command and swarm orchestration endpoints."""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.orm import Earthquake, RiskPrediction, SensorStation
from app.models.schemas import CommandOverviewOut, SwarmPlanOut
from app.services.command_layer import build_command_overview, build_swarm_plan
from app.services.sensor_service import confirm_tsunami_anomaly

logger = logging.getLogger("tsunami.api.command")
router = APIRouter(prefix="/command", tags=["command"])


@router.get("/overview/{earthquake_id}", response_model=CommandOverviewOut, summary="Digital-twin command overview")
async def get_command_overview(earthquake_id: str, db: AsyncSession = Depends(get_db)):
    earthquake = await db.get(Earthquake, earthquake_id)
    if not earthquake:
        raise HTTPException(status_code=404, detail=f"Earthquake {earthquake_id} not found")

    stmt = (
        select(RiskPrediction)
        .where(RiskPrediction.earthquake_id == earthquake_id)
        .order_by(RiskPrediction.predicted_at.desc())
    )
    result = await db.execute(stmt)
    latest_prediction = result.scalars().first()
    if not latest_prediction:
        raise HTTPException(status_code=404, detail=f"No risk prediction found for {earthquake_id}")

    active_station_count = await db.scalar(
        select(func.count(SensorStation.id)).where(SensorStation.status == "ACTIVE")
    )

    confirmed, _ = await confirm_tsunami_anomaly(db, earthquake.latitude, earthquake.longitude)

    overview = build_command_overview(
        event_id=earthquake.id,
        risk_level=latest_prediction.risk_level,
        risk_score=latest_prediction.risk_score,
        place=earthquake.place,
        station_count=active_station_count or 0,
        confirmed_by_sensor=confirmed,
    )
    return overview


@router.get("/swarm/{earthquake_id}", response_model=SwarmPlanOut, summary="Swarm plan for emergency response")
async def get_swarm_plan(earthquake_id: str, db: AsyncSession = Depends(get_db)):
    earthquake = await db.get(Earthquake, earthquake_id)
    if not earthquake:
        raise HTTPException(status_code=404, detail=f"Earthquake {earthquake_id} not found")

    stmt = (
        select(RiskPrediction)
        .where(RiskPrediction.earthquake_id == earthquake_id)
        .order_by(RiskPrediction.predicted_at.desc())
    )
    result = await db.execute(stmt)
    latest_prediction = result.scalars().first()
    if not latest_prediction:
        raise HTTPException(status_code=404, detail=f"No risk prediction found for {earthquake_id}")

    swarm_plan = build_swarm_plan(
        event_id=earthquake.id,
        risk_level=latest_prediction.risk_level,
        risk_score=latest_prediction.risk_score,
        place=earthquake.place,
        magnitude=earthquake.magnitude,
    )
    return swarm_plan
