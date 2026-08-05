"""
API Router for Layer 1 — Sensing & Data Acquisition
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from app.services.data_sim_engine import sim_engine

router = APIRouter(prefix="/api/sensors", tags=["Layer 1 — Sensing"])

class TriggerEventRequest(BaseModel):
    magnitude: float = Field(default=7.8, ge=5.0, le=9.5, description="Earthquake moment magnitude (Mw)")
    distance_km: float = Field(default=45.0, ge=5.0, le=500.0, description="Epicenter distance from coast in km")

@router.get("/snapshot")
async def get_sensor_snapshot():
    return sim_engine.get_latest_snapshot()

@router.get("/bathymetry")
async def get_bathymetry_grid():
    return {
        "grid_size": 50,
        "grid": sim_engine.get_bathymetry_grid()
    }

@router.post("/trigger-event")
async def trigger_event(req: TriggerEventRequest):
    sim_engine.trigger_event(magnitude=req.magnitude, distance_km=req.distance_km)
    return {
        "status": "EVENT_INJECTED",
        "message": f"Earthquake scenario injected: M{req.magnitude} at {req.distance_km}km distance.",
        "snapshot": sim_engine.get_latest_snapshot()
    }

@router.post("/reset")
async def reset_simulation():
    sim_engine.reset_simulation()
    return {
        "status": "RESET",
        "message": "Simulation returned to nominal baseline state."
    }
