"""
API Router for V2 Extension 1 — Real Public Data Integration
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from app.services.live_data_service import live_data_service

router = APIRouter(prefix="/api/live-data", tags=["V2 — Real Public Data Integration"])

class ToggleModeRequest(BaseModel):
    mode: str = Field(default="SIMULATED", description="Data mode: SIMULATED or LIVE_PUBLIC_FEEDS")

@router.get("/status")
async def get_live_data_status():
    return await live_data_service.get_live_data_snapshot()

@router.post("/toggle")
async def toggle_data_mode(req: ToggleModeRequest):
    return live_data_service.set_mode(req.mode)
