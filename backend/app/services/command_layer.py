"""Command-and-control orchestration helpers for the digital-twin tsunami platform.

These functions keep the paper-aligned command architecture lightweight and
fully deterministic so the backend can expose it without needing any extra
infrastructure at runtime.
"""

from __future__ import annotations


def build_command_overview(
    event_id: str,
    risk_level: str,
    risk_score: float,
    place: str,
    station_count: int = 0,
    confirmed_by_sensor: bool = False,
) -> dict:
    """Create a compact command overview for the dashboard and API consumers."""
    confidence = min(0.99, 0.55 + (risk_score * 0.35) + (0.1 if confirmed_by_sensor else 0.0))

    if risk_level in {"HIGH", "SEVERE"} or risk_score >= 0.72:
        response_priority = "EVACUATE"
    elif risk_level == "MODERATE" or risk_score >= 0.45:
        response_priority = "PREPARE"
    else:
        response_priority = "MONITOR"

    digital_twin_status = "LINKED" if risk_score >= 0.6 else "SIMULATING"

    return {
        "event_id": event_id,
        "place": place,
        "digital_twin_status": digital_twin_status,
        "response_priority": response_priority,
        "telemetry_confidence": round(confidence, 3),
        "station_count": station_count,
        "sensor_confirmed": confirmed_by_sensor,
        "risk_level": risk_level,
        "risk_score": round(risk_score, 3),
    }


def build_swarm_plan(
    event_id: str,
    risk_level: str,
    risk_score: float,
    place: str,
    magnitude: float,
) -> dict:
    """Return a deterministic swarm plan mirroring the paper's command flow."""
    if risk_level == "SEVERE" or risk_score >= 0.8:
        command_mode = "FULL_RESPONSE"
        decision_summary = f"Issue evacuation guidance and activate coastal response squads for {place}."
    elif risk_level == "HIGH" or risk_score >= 0.6:
        command_mode = "PREPAREDNESS"
        decision_summary = f"Coordinate sheltering and rapid wave-projection checks for {place}."
    else:
        command_mode = "SURVEILLANCE"
        decision_summary = f"Maintain constant sensor monitoring and keep public advisories on standby for {place}."

    agents = [
        {
            "role": "forecast-swarm",
            "owner": "Wave Propagation Cell",
            "mission": "Project travel time and inundation envelopes",
            "priority": "high",
        },
        {
            "role": "telemetry-swarm",
            "owner": "Sensor Fusion Cell",
            "mission": "Confirm anomaly signatures from offshore buoys and tide gauges",
            "priority": "critical" if risk_level in {"HIGH", "SEVERE"} else "medium",
        },
        {
            "role": "evacuation-swarm",
            "owner": "Public Safety Cell",
            "mission": "Disseminate routes, shelters, and public warning notices",
            "priority": "critical" if risk_level in {"HIGH", "SEVERE"} else "medium",
        },
        {
            "role": "command-swarm",
            "owner": "Operations Desk",
            "mission": "Track the evolving event and maintain the digital twin state",
            "priority": "medium",
        },
    ]

    return {
        "event_id": event_id,
        "command_mode": command_mode,
        "decision_summary": decision_summary,
        "place": place,
        "magnitude": magnitude,
        "risk_level": risk_level,
        "risk_score": round(risk_score, 3),
        "agents": agents,
    }
