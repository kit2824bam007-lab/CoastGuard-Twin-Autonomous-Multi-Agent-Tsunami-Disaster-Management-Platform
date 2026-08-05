"""
API Router for Layer 5 — Decision Support & Alerting
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Dict, Any
from app.services.data_sim_engine import sim_engine
from app.services.digital_twin import digital_twin_service
from app.services.ml_classifier import ml_classifier, ConsoleAlertChannel

router = APIRouter(prefix="/api/alerts", tags=["Layer 5 — Decision Support & Alerts"])

class DispatchAlertRequest(BaseModel):
    title: str = Field(default="TSUNAMI WARNING")
    message: str = Field(default="Evacuate coastal lowlands immediately toward high ground!")
    severity: str = Field(default="SEVERE")

@router.get("/severity")
async def get_current_hazard_severity():
    snapshot = sim_engine.get_latest_snapshot()
    twin_state = digital_twin_service.get_current_twin_state()
    
    p_wave = snapshot["sensors"]["seismic"]["p_wave"]
    s_wave = snapshot["sensors"]["seismic"]["s_wave"]
    buoy_anomaly = snapshot["sensors"]["dart_buoy"]["sea_level_anomaly_m"]
    shoreline_state = snapshot["sensors"]["shoreline_camera"]["state"]
    max_inundation = twin_state["summary"]["max_inundation_depth_m"]
    distance_km = snapshot["event_params"]["distance_km"]

    # ML Classifier inference
    classification = ml_classifier.predict(
        p_wave=p_wave,
        s_wave=s_wave,
        buoy_anomaly=buoy_anomaly,
        shoreline_state=shoreline_state,
        max_inundation=max_inundation,
        distance_km=distance_km
    )

    # Calculate estimated wave arrival time (ETA in minutes)
    eta_minutes = round(max(1.0, distance_km * 0.4), 1) if snapshot["is_event_active"] else None

    # Directions & evacuation shelters
    shelter_recommendation = {
        "shelter_name": "Highland Sanctuary Complex",
        "distance_km": 2.4,
        "heading_degrees": 45, # North-East inland
        "direction_label": "NE Inland",
        "safe_elevation_m": 85
    }

    return {
        "classification": classification,
        "is_event_active": snapshot["is_event_active"],
        "estimated_wave_eta_minutes": eta_minutes,
        "max_inundation_m": max_inundation,
        "affected_zones": ["Coastal Zone A", "Lowland Sector 2"] if classification["severity_index"] >= 2 else [],
        "civilian_instructions": (
            "EMERGENCY EVACUATION ORDER: Move to inland elevation above 50m immediately!" 
            if classification["severity_index"] == 3 else
            ("Tsunami Watch: Prepare evacuation kits and monitor emergency broadcast."
             if classification["severity_index"] >= 1 else "Normal coastal conditions. No active threat detected.")
        ),
        "nearest_shelter": shelter_recommendation
    }

@router.post("/dispatch")
async def dispatch_alert(req: DispatchAlertRequest):
    channel = ConsoleAlertChannel()
    result = channel.dispatch(req.title, req.message, req.severity)
    return {
        "status": "SUCCESS",
        "dispatch": result
    }
