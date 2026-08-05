"""
API Router for Layer 2 — Digital Twin Synchronization
"""
from fastapi import APIRouter, Query
from typing import Dict, Any, List
from app.services.digital_twin import digital_twin_service

router = APIRouter(prefix="/api/twin", tags=["Layer 2 — Digital Twin"])

@router.get("/state")
async def get_twin_state():
    return digital_twin_service.get_current_twin_state()

@router.get("/history")
async def get_twin_history(range_limit: int = Query(default=50, ge=1, le=300)):
    return {
        "count": len(digital_twin_service.snapshots_history[-range_limit:]),
        "snapshots": digital_twin_service.snapshots_history[-range_limit:]
    }
