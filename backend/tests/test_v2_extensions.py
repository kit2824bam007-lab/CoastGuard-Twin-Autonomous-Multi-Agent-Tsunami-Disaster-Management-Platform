"""
Unit & Integration Tests for CoastGuard Twin Version 2 Real-World Extensions
"""
import asyncio
import pytest
from app.services.live_data_service import live_data_service
from app.services.authority_bridge import authority_bridge
from app.services.federated_learning import federated_learning_service
from app.services.replay_service import replay_service
from app.services.extended_alerts import TwilioSMSAlertChannel, FirebasePushAlertChannel
from app.services.swarm_engine import swarm_engine

def test_v2_live_data_service():
    # Default SIMULATED mode
    assert live_data_service.mode == "SIMULATED"
    
    # Toggle LIVE mode
    res = live_data_service.set_mode("LIVE_PUBLIC_FEEDS")
    assert res["mode"] == "LIVE_PUBLIC_FEEDS"
    assert "safety_notice" in res

    # Fetch snapshot using asyncio.run
    snapshot = asyncio.run(live_data_service.get_live_data_snapshot())
    assert "usgs_quakes_count" in snapshot
    assert snapshot["mode"] == "LIVE_PUBLIC_FEEDS"

    # Reset mode
    live_data_service.set_mode("SIMULATED")

def test_v2_authority_bridge_and_audit_log():
    # Test CAP v1.2 export
    cap = authority_bridge.generate_cap_export(
        hazard_classification={"predicted_class": "SEVERE"},
        twin_summary={"max_inundation_depth_m": 3.4, "high_risk_cells_count": 12},
        swarm_topology={"nodes": [{"type": "UAV", "status": "ACTIVE"}]},
        operator_id="OP-TEST-99"
    )

    assert cap["cap_version"] == "1.2"
    assert cap["alert"]["info"]["severity"] == "Extreme"
    assert "INCOIS" in cap["target_authorities"][0]

    # Test audit ledger
    ledger = authority_bridge.get_audit_ledger()
    assert len(ledger) > 0
    latest_event = ledger[-1]
    assert latest_event["operator_id"] == "OP-TEST-99"
    assert "CAP_ALERT_EXPORTED" in latest_event["event_type"]

def test_v2_federated_learning():
    initial_status = federated_learning_service.get_fl_status()
    assert len(initial_status["regional_twins"]) == 3
    
    # Run 1 FedAvg round
    round_result = federated_learning_service.run_federated_round()
    assert round_result["round_number"] > 0
    assert round_result["global_accuracy"] >= 0.90

def test_v2_replay_service():
    sessions = replay_service.list_sessions()
    assert len(sessions) > 0
    demo_session_id = sessions[0]["session_id"]
    
    timeline = replay_service.get_session_timeline(demo_session_id)
    assert timeline is not None
    assert len(timeline["frames"]) == 30
    assert timeline["frames"][0]["frame_index"] == 0

def test_v2_extended_alerts():
    sms_channel = TwilioSMSAlertChannel()
    res_sms = sms_channel.dispatch("TSUNAMI TEST", "Evacuate high ground", "SEVERE")
    assert res_sms["status"] == "SANDBOX_MOCK_SUCCESS"

    fcm_channel = FirebasePushAlertChannel()
    res_fcm = fcm_channel.dispatch("TSUNAMI TEST", "Evacuate high ground", "SEVERE")
    assert res_fcm["channel"] == "firebase_push"

def test_v2_satellite_failover():
    # Toggle LEO satellite failover
    active = swarm_engine.toggle_satellite_failover(True)
    assert active is True

    topology = swarm_engine.update_mesh_topology()
    assert topology["is_satellite_failover_active"] is True
    assert topology["channel_type"] == "LEO_SATELLITE"

    # Reset
    swarm_engine.toggle_satellite_failover(False)
