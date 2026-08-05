"""
API Router for V2 Extension 2 — Official-Authority Handoff & Audit Log
"""
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from app.services.authority_bridge import authority_bridge
from app.services.digital_twin import digital_twin_service
from app.services.swarm_engine import swarm_engine
from app.services.ml_classifier import ml_classifier

router = APIRouter(prefix="/api/authority", tags=["V2 — Official-Authority Handoff"])

class LogActionRequest(BaseModel):
    action: str = Field(..., description="Action e.g. AGENT_REASSIGNMENT, ALERT_DISPATCH")
    details: str = Field(...)
    operator_id: str = Field(default="OP-101")

@router.get("/export-cap")
async def export_cap_alert(operator_id: str = Query(default="OP-101")):
    twin_state = digital_twin_service.get_current_twin_state()
    topology = swarm_engine.update_mesh_topology()
    
    # Infer hazard classification
    snapshot = twin_state["fused_sensors"]
    p_wave = snapshot["seismic"]["p_wave"]
    s_wave = snapshot["seismic"]["s_wave"]
    buoy = snapshot["dart_buoy"]["sea_level_anomaly_m"]
    shore = snapshot["shoreline_camera"]["state"]
    max_inundation = twin_state["summary"]["max_inundation_depth_m"]
    dist_km = twin_state["event_params"]["distance_km"]

    classification = ml_classifier.predict(p_wave, s_wave, buoy, shore, max_inundation, dist_km)

    return authority_bridge.generate_cap_export(
        hazard_classification=classification,
        twin_summary=twin_state["summary"],
        swarm_topology=topology,
        operator_id=operator_id
    )

@router.get("/audit-log")
async def get_audit_log(limit: int = Query(default=50, ge=1, le=200)):
    return {
        "count": len(authority_bridge.get_audit_ledger(limit)),
        "audit_log": authority_bridge.get_audit_ledger(limit)
    }

@router.post("/log-action")
async def log_operator_action(req: LogActionRequest):
    authority_bridge.log_operator_action(req.action, req.details, req.operator_id)
    return {"status": "LOGGED"}
