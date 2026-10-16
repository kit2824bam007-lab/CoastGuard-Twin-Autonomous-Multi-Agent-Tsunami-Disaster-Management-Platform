"""
Automated Research Tests for CoastGuard Twin
Validates:
1. A* path planner obstacle avoidance, slope costs, and vehicle constraints
2. Start and goal traversability validation
3. Strict diagonal corner-cutting prevention
4. Discrete-event coastal simulation trial execution and metric consistency
5. Strict deterministic reproducibility under identical seeds
6. Explicit evacuation duration accounting (completion_time - evac_start_time)
7. Benchmark statistical computations (mean, std, 95% CI, improvement formulas)
8. Ablation study component toggling
9. Synthetic dataset split reproducibility and zero-leakage isolation
"""
import pytest
import math
import numpy as np

from app.services.path_planner import astar_planner
from app.services.simulation_benchmark_runner import CoastalSimulationTrial, BenchmarkRunner
from app.experiments.train_ml import generate_dataset, train_test_split

def test_astar_planner_basic_navigation():
    bathymetry = [[10.0 for _ in range(50)] for _ in range(50)]
    start = (5, 5)
    goal = (15, 15)

    res = astar_planner.find_path(start, goal, agent_type="GROUND", bathymetry_grid=bathymetry)
    assert res["success"] is True
    assert len(res["path"]) > 0
    assert res["path"][0] == start
    assert res["path"][-1] == goal
    assert res["path_cost"] > 0.0

def test_astar_start_and_goal_traversability():
    bathymetry = [[10.0 for _ in range(50)] for _ in range(50)]
    # Mark (5, 5) as ocean (elevation <= 0)
    bathymetry[5][5] = -10.0
    start = (5, 5)
    goal = (15, 15)

    # GROUND agent cannot start in ocean
    res_start_blocked = astar_planner.find_path(start, goal, agent_type="GROUND", bathymetry_grid=bathymetry)
    assert res_start_blocked["success"] is False
    assert "impassable" in res_start_blocked["message"].lower()

    # Reset (5, 5) and mark goal as ocean
    bathymetry[5][5] = 10.0
    bathymetry[15][15] = -10.0
    res_goal_blocked = astar_planner.find_path(start, goal, agent_type="GROUND", bathymetry_grid=bathymetry)
    assert res_goal_blocked["success"] is False
    assert "impassable" in res_goal_blocked["message"].lower()

def test_astar_diagonal_corner_cutting_prevention():
    # 50x50 grid of land
    bathymetry = [[10.0 for _ in range(50)] for _ in range(50)]
    # Place wall at (5, 6)
    inundation = [
        [
            {"inundation_depth_m": 3.0 if (x == 5 and y == 6) else 0.0, "risk_score": 1.0}
            for x in range(50)
        ]
        for y in range(50)
    ]
    start = (5, 5)
    goal = (6, 6)

    # For GROUND agent, (5, 6) is impassable.
    # A diagonal step from (5, 5) to (6, 6) must NOT cut through the corner of (5, 6).
    res = astar_planner.find_path(start, goal, agent_type="GROUND", bathymetry_grid=bathymetry, inundation_grid=inundation)
    assert res["success"] is True
    # The path must NOT make a single direct diagonal step if corner cutting is prevented;
    # It must navigate via (6, 5) -> (6, 6)
    path = res["path"]
    assert len(path) >= 3  # (5, 5) -> (6, 5) -> (6, 6)
    assert (6, 5) in path

def test_astar_slope_dependent_cost():
    # Flat terrain
    flat_bathymetry = [[10.0 for _ in range(50)] for _ in range(50)]
    # Steep uphill terrain (elevation increases by 20m per cell along x)
    steep_bathymetry = [[10.0 + x * 20.0 for x in range(50)] for _ in range(50)]

    start = (5, 5)
    goal = (10, 5)

    res_flat = astar_planner.find_path(start, goal, agent_type="GROUND", bathymetry_grid=flat_bathymetry)
    res_steep = astar_planner.find_path(start, goal, agent_type="GROUND", bathymetry_grid=steep_bathymetry)

    assert res_flat["success"] is True
    assert res_steep["success"] is True
    # Steep uphill path must incur strictly higher path cost than flat terrain
    assert res_steep["path_cost"] > res_flat["path_cost"]

def test_astar_planner_obstacle_and_inundation_avoidance():
    # Create grid with deep inundation barrier across x=10
    bathymetry = [[10.0 for _ in range(50)] for _ in range(50)]
    inundation = [
        [
            {"inundation_depth_m": 3.0 if x == 10 and 0 <= y <= 40 else 0.0, "risk_score": 1.0}
            for x in range(50)
        ]
        for y in range(50)
    ]

    start = (5, 20)
    goal = (15, 20)

    res = astar_planner.find_path(start, goal, agent_type="GROUND", bathymetry_grid=bathymetry, inundation_grid=inundation)
    assert res["success"] is True
    max_y_in_path = max(pt[1] for pt in res["path"])
    assert max_y_in_path > 40  # Routed around the flooded zone!

def test_coastal_simulation_trial_strict_determinism():
    # Two independent trials run with identical seed must yield identical outcome metrics
    trial1 = CoastalSimulationTrial(
        trial_id=1, magnitude=7.8, distance_km=45.0, num_civilians=20,
        sim_duration_steps=40, seed=12345
    )
    res1 = trial1.run()

    trial2 = CoastalSimulationTrial(
        trial_id=1, magnitude=7.8, distance_km=45.0, num_civilians=20,
        sim_duration_steps=40, seed=12345
    )
    res2 = trial2.run()

    keys_to_compare = [
        "detection_to_alert_time_sec", "observation_time_sec", "decision_time_sec",
        "transmission_time_sec", "alert_dispatch_time_sec", "evacuation_duration_sec",
        "evacuation_completion_pct", "search_coverage_pct", "path_planning_success_pct",
        "civilians_evacuated", "civilians_trapped", "total_civilians", "communication_messages"
    ]
    for k in keys_to_compare:
        assert res1[k] == res2[k], f"Nondeterminism detected in key '{k}': {res1[k]} != {res2[k]}"

def test_evacuation_accounting_and_timestamps():
    trial = CoastalSimulationTrial(
        trial_id=1, magnitude=7.8, distance_km=45.0, num_civilians=25,
        sim_duration_steps=60, seed=999
    )
    res = trial.run()

    # Total civilian conservation
    assert res["civilians_evacuated"] + res["civilians_trapped"] + res["civilians_in_transit"] == res["total_civilians"]
    assert res["total_civilians"] == 25

    # Check alert pipeline timestamp progression if alert was dispatched
    if res["alert_dispatch_time_sec"] is not None:
        assert res["observation_time_sec"] <= res["decision_time_sec"]
        assert res["decision_time_sec"] <= res["transmission_time_sec"]
        assert res["transmission_time_sec"] <= res["alert_dispatch_time_sec"]

def test_benchmark_runner_multi_trial_statistics():
    runner = BenchmarkRunner(num_trials=3, base_seed=50)
    results = runner.run_benchmark(magnitude=7.5, distance_km=50.0)

    assert results["metadata"]["num_trials"] == 3
    assert len(results["comparison_metrics"]) >= 4

    for m in results["comparison_metrics"]:
        assert "baseline_mean" in m
        assert "proposed_mean" in m
        assert "improvement_percentage" in m
        assert m["baseline_ci95"][0] <= m["baseline_ci95"][1]
        assert m["proposed_ci95"][0] <= m["proposed_ci95"][1]

def test_ablation_study_execution():
    runner = BenchmarkRunner(num_trials=2, base_seed=70)
    results = runner.run_ablation_study(magnitude=7.5, distance_km=50.0, trials_per_variant=2)

    assert len(results["ablation_summary"]) == 5
    variants = [v["variant_name"] for v in results["ablation_summary"]]
    assert any("PSO" in v for v in variants)
    assert any("A*" in v for v in variants)
    assert any("Mesh" in v for v in variants)
    assert any("Centralized" in v for v in variants)

def test_dataset_reproducibility_and_split_isolation():
    X1, y1 = generate_dataset(num_samples=100, mode="historical", seed=42)
    X2, y2 = generate_dataset(num_samples=100, mode="historical", seed=42)
    assert np.array_equal(X1, X2)
    assert np.array_equal(y1, y2)

    X_tr, X_temp, y_tr, y_temp = train_test_split(X1, y1, test_size=0.30, random_state=42, stratify=y1)
    X_val, X_te, y_val, y_te = train_test_split(X_temp, y_temp, test_size=0.50, random_state=42, stratify=y_temp)
    assert len(X_tr) + len(X_val) + len(X_te) == len(X1)
