"""
Unit & Integration Tests for CoastGuard Twin 5-Layer Platform
"""
import pytest
from app.services.data_sim_engine import sim_engine, GRID_SIZE
from app.services.digital_twin import digital_twin_service
from app.services.swarm_engine import swarm_engine
from app.services.ml_classifier import ml_classifier
from app.services.benchmark_service import benchmark_service

def test_layer1_sensing_engine():
    # Reset and check initial state
    sim_engine.reset_simulation()
    snapshot = sim_engine.get_latest_snapshot()
    
    assert snapshot["is_event_active"] is False
    assert snapshot["sensors"]["shoreline_camera"]["state"] == "NORMAL"
    assert len(sim_engine.get_bathymetry_grid()) == GRID_SIZE
    assert len(sim_engine.get_bathymetry_grid()[0]) == GRID_SIZE

    # Trigger event
    sim_engine.trigger_event(magnitude=7.8, distance_km=45.0)
    event_snapshot = sim_engine.tick()
    
    assert event_snapshot["is_event_active"] is True
    assert event_snapshot["event_params"]["magnitude"] == 7.8
    assert event_snapshot["event_params"]["distance_km"] == 45.0

def test_layer2_digital_twin():
    sensor_snapshot = sim_engine.get_latest_snapshot()
    twin_state = digital_twin_service.get_current_twin_state()
    
    assert "summary" in twin_state
    assert "risk_grid" in twin_state
    assert len(twin_state["risk_grid"]) == GRID_SIZE
    assert len(twin_state["risk_grid"][0]) == GRID_SIZE
    assert "max_inundation_depth_m" in twin_state["summary"]

def test_layer3_swarm_engine():
    topology = swarm_engine.update_mesh_topology()
    
    assert topology["total_active"] > 0
    assert len(topology["nodes"]) >= 9 # 3 UAV, 3 USV, 3 Ground
    assert "edges" in topology

    # Test deploy agent
    new_agent = swarm_engine.deploy_agent("UAV", 20.0, 20.0)
    assert new_agent.id.startswith("UAV-")
    assert new_agent.status == "ACTIVE"

    # Test simulate agent loss
    swarm_engine.simulate_agent_loss("UAV-101")
    assert swarm_engine.agents["UAV-101"].status == "LOST"

def test_layer5_ml_classifier_and_metrics():
    classification = ml_classifier.predict(
        p_wave=1.2,
        s_wave=2.5,
        buoy_anomaly=1.9,
        shoreline_state="SURGING",
        max_inundation=3.5,
        distance_km=45.0
    )
    
    assert classification["predicted_class"] in ["NO_THREAT", "WATCH", "WARNING", "SEVERE"]
    assert classification["confidence"] > 0.0

    metrics = ml_classifier.latest_metrics
    assert metrics["accuracy"] >= 0.85
    assert len(metrics["confusion_matrix_percentage"]) == 4

def test_benchmark_service():
    benchmark = benchmark_service.run_live_comparison(is_event_active=True, event_magnitude=7.8)
    assert len(benchmark["metrics"]) == 4
    for m in benchmark["metrics"]:
        assert "baseline" in m
        assert "proposed_swarm" in m
        assert "improvement_percentage" in m
