import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.command_layer import build_command_overview, build_swarm_plan


def test_build_swarm_plan_returns_priority_agents():
    overview = build_swarm_plan(
        event_id="test-event-1",
        risk_level="SEVERE",
        risk_score=0.93,
        place="Rakata Strait",
        magnitude=8.6,
    )

    assert overview["command_mode"] == "FULL_RESPONSE"
    assert any(agent["role"] == "forecast-swarm" for agent in overview["agents"])
    assert any(agent["role"] == "evacuation-swarm" for agent in overview["agents"])
    assert overview["decision_summary"].startswith("Issue")


def test_build_command_overview_returns_actionable_summary():
    summary = build_command_overview(
        event_id="test-event-1",
        risk_level="HIGH",
        risk_score=0.72,
        place="Sunda Strait",
        station_count=5,
        confirmed_by_sensor=True,
    )

    assert summary["digital_twin_status"] in {"LINKED", "SIMULATING"}
    assert summary["response_priority"] in {"PREPARE", "EVACUATE"}
    assert summary["telemetry_confidence"] >= 0.5
