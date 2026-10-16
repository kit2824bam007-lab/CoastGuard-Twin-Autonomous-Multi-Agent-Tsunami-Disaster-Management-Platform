"""
Metrics Dashboard Engine — Centralized Baseline vs. Proposed Multi-Agent System
Computes live comparative benchmark metrics matching paper Table 1 / Figure 7:
- Detection-to-Alert Time (s)
- Average Evacuation Time (min)
- Search-Area Coverage (%)
- Path-Planning Success Rate (%)
"""
import random
import time
from typing import Dict, Any, List
from app.services.simulation_benchmark_runner import CoastalSimulationTrial

class BenchmarkService:
    def __init__(self):
        self.last_run_time = None
        self.cached_simulation_results: Dict[str, Any] = {}
        self.benchmark_results = self._generate_benchmark_comparison()

    def _generate_benchmark_comparison(
        self,
        is_event_active: bool = False,
        event_magnitude: float = 7.8,
        use_real_simulation: bool = True
    ) -> Dict[str, Any]:
        """
        Calculates comparative metric evaluation between:
        1. Centralized Single-Node Baseline System
        2. Proposed Decentralized Swarm Digital Twin System
        When use_real_simulation=True, executes identical discrete-event trials over the 50x50 coastal grid.
        """
        if use_real_simulation:
            # Run genuine simulation trials with fixed deterministic seed for reproducible API calls
            seed = 42 if not is_event_active else int(event_magnitude * 100)
            trial_base = CoastalSimulationTrial(
                trial_id=1,
                magnitude=event_magnitude,
                distance_km=45.0,
                is_centralized_baseline=True,
                enable_pso=False,
                enable_astar=True,
                enable_mesh=False,
                seed=seed
            )
            res_base = trial_base.run()

            trial_swarm = CoastalSimulationTrial(
                trial_id=1,
                magnitude=event_magnitude,
                distance_km=45.0,
                is_centralized_baseline=False,
                enable_pso=True,
                enable_astar=True,
                enable_mesh=True,
                seed=seed
            )
            res_swarm = trial_swarm.run()

            base_detection_time = res_base["detection_to_alert_time_sec"]
            swarm_detection_time = res_swarm["detection_to_alert_time_sec"]

            base_evac_time = res_base["evacuation_time_min"]
            swarm_evac_time = res_swarm["evacuation_time_min"]

            base_coverage = res_base["search_coverage_pct"]
            swarm_coverage = res_swarm["search_coverage_pct"]

            base_path_success = res_base["path_planning_success_pct"]
            swarm_path_success = res_swarm["path_planning_success_pct"]
        else:
            # Historical analytical baseline generator
            base_detection_time = round(145.0 + random.uniform(-10.0, 15.0) + (10.0 - event_magnitude) * 5.0, 1)
            base_evac_time = round(38.5 + random.uniform(-3.0, 5.0), 1)
            base_coverage = round(62.4 + random.uniform(-4.0, 4.0), 1)
            base_path_success = round(74.2 + random.uniform(-5.0, 5.0), 1)

            swarm_detection_time = round(32.0 + random.uniform(-3.0, 4.0), 1)
            swarm_evac_time = round(19.2 + random.uniform(-1.5, 2.0), 1)
            swarm_coverage = round(96.8 + random.uniform(-1.5, 1.5), 1)
            swarm_path_success = round(98.4 + random.uniform(-1.0, 1.0), 1)

        det_imp = round(((base_detection_time - swarm_detection_time) / base_detection_time) * 100, 1) if base_detection_time > 0 else 0.0
        evac_imp = round(((base_evac_time - swarm_evac_time) / base_evac_time) * 100, 1) if base_evac_time > 0 else 0.0
        cov_imp = round(((swarm_coverage - base_coverage) / base_coverage) * 100, 1) if base_coverage > 0 else 0.0
        path_imp = round(((swarm_path_success - base_path_success) / base_path_success) * 100, 1) if base_path_success > 0 else 0.0

        return {
            "timestamp": round(time.time(), 2),
            "is_event_active": is_event_active,
            "evaluation_engine": "discrete_event_coastal_simulation" if use_real_simulation else "historical_heuristic",
            "metrics": [
                {
                    "key": "detection_time_sec",
                    "title": "Detection-to-Alert Time",
                    "unit": "seconds",
                    "baseline": base_detection_time,
                    "proposed_swarm": swarm_detection_time,
                    "improvement_percentage": det_imp,
                    "lower_is_better": True
                },
                {
                    "key": "avg_evac_time_min",
                    "title": "Average Evacuation Time",
                    "unit": "minutes",
                    "baseline": base_evac_time,
                    "proposed_swarm": swarm_evac_time,
                    "improvement_percentage": evac_imp,
                    "lower_is_better": True
                },
                {
                    "key": "coverage_percentage",
                    "title": "Search-Area Coverage",
                    "unit": "%",
                    "baseline": base_coverage,
                    "proposed_swarm": swarm_coverage,
                    "improvement_percentage": cov_imp,
                    "lower_is_better": False
                },
                {
                    "key": "path_success_rate",
                    "title": "Path-Planning Success Rate",
                    "unit": "%",
                    "baseline": base_path_success,
                    "proposed_swarm": swarm_path_success,
                    "improvement_percentage": path_imp,
                    "lower_is_better": False
                }
            ]
        }

    def run_live_comparison(self, is_event_active: bool = False, event_magnitude: float = 7.5) -> Dict[str, Any]:
        self.benchmark_results = self._generate_benchmark_comparison(is_event_active, event_magnitude, use_real_simulation=True)
        return self.benchmark_results

benchmark_service = BenchmarkService()
