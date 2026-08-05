"""
API Router for V2 Extension 7 — Historical Replay & Responder Training
"""
from fastapi import APIRouter, HTTPException
from app.services.replay_service import replay_service

router = APIRouter(prefix="/api/replay", tags=["V2 — Historical Replay"])

@router.get("/sessions")
async def list_replay_sessions():
    return {"sessions": replay_service.list_sessions()}

@router.get("/timeline/{session_id}")
async def get_session_timeline(session_id: str):
    timeline = replay_service.get_session_timeline(session_id)
    if not timeline:
        raise HTTPException(status_code=404, detail=f"Replay session '{session_id}' not found.")
    return timeline
