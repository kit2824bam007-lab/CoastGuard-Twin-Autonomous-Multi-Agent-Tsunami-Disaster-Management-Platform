"""
Ablation Study Experiment Runner for CoastGuard Twin
Evaluates individual contributions of system components:
1. Full Proposed Multi-Agent System (Swarm + PSO + A* + Dynamic Mesh)
2. Swarm without PSO-based Coordination (Random Walk / Fixed Patrol)
3. Swarm without A* Path Planning (Direct Line Trajectories)
4. Swarm without Dynamic Mesh Communication (Isolated Local Agents)
5. Centralized Baseline (Single Hub Dispatch Controller)

Exports trial logs, ablation summary table, CSVs, and JSON to results/ablation/
"""
import os
import sys
import csv
import json
import argparse

backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from app.services.simulation_benchmark_runner import BenchmarkRunner

def run_ablation_study(
    trials_per_variant: int = 15,
    magnitude: float = 7.8,
    distance_km: float = 45.0,
    base_seed: int = 200,
    output_dir: str = None
):
    if output_dir is None:
        output_dir = os.path.join(backend_root, "..", "results", "ablation")
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 75)
    print(f"RUNNING COMPONENT ABLATION STUDY ({trials_per_variant} Trials per Variant)")
    print(f"Scenario: Magnitude {magnitude}, Distance {distance_km} km")
    print("=" * 75)

    runner = BenchmarkRunner(num_trials=trials_per_variant, base_seed=base_seed)
    results = runner.run_ablation_study(
        magnitude=magnitude,
        distance_km=distance_km,
        trials_per_variant=trials_per_variant
    )

    # 1. Export Ablation Summary CSV
    csv_path = os.path.join(output_dir, f"ablation_summary_m{magnitude}_d{distance_km}_n{trials_per_variant}.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Ablation_Variant", "PSO_Enabled", "AStar_Enabled", "Mesh_Enabled", "Is_Centralized",
            "Detection_Time_s_Mean", "Detection_Time_s_Std",
            "Evacuation_Time_min_Mean", "Evacuation_Time_min_Std",
            "Search_Coverage_pct_Mean", "Search_Coverage_pct_Std",
            "Path_Planning_Success_pct_Mean", "Path_Planning_Success_pct_Std",
            "Evacuation_Success_pct_Mean", "Evacuation_Success_pct_Std"
        ])
        for var in results["ablation_summary"]:
            m = var["metrics"]
            writer.writerow([
                var["variant_name"], var["pso_enabled"], var["astar_enabled"], var["mesh_enabled"], var["is_centralized"],
                m["detection_time_mean"], m["detection_time_std"],
                m["evacuation_time_mean"], m["evacuation_time_std"],
                m["coverage_mean"], m["coverage_std"],
                m["path_success_mean"], m["path_success_std"],
                m["evacuation_success_mean"], m["evacuation_success_std"]
            ])

    # 2. Export Full JSON Report with Raw Trials
    json_path = os.path.join(output_dir, f"ablation_report_m{magnitude}_d{distance_km}_n{trials_per_variant}.json")
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2)

    # Print Clean Console Summary Table
    print("\nABLATION EXPERIMENT RESULTS:")
    print("-" * 105)
    print(f"{'Variant':<38} | {'Det Latency (s)':<16} | {'Evac Time (m)':<14} | {'Coverage (%)':<14} | {'Path Succ (%)':<14}")
    print("-" * 105)
    for var in results["ablation_summary"]:
        m = var["metrics"]
        det_str = f"{m['detection_time_mean']} ± {m['detection_time_std']}"
        evac_str = f"{m['evacuation_time_mean']} ± {m['evacuation_time_std']}"
        cov_str = f"{m['coverage_mean']} ± {m['coverage_std']}"
        path_str = f"{m['path_success_mean']} ± {m['path_success_std']}"
        print(f"{var['variant_name']:<38} | {det_str:<16} | {evac_str:<14} | {cov_str:<14} | {path_str:<14}")
    print("-" * 105)
    print(f"\nSaved Ablation Summary CSV: {csv_path}")
    print(f"Saved Full JSON Report:     {json_path}")

    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run CoastGuard Twin Ablation Studies")
    parser.add_argument("--trials", type=int, default=15, help="Number of trials per variant")
    parser.add_argument("--magnitude", type=float, default=7.8, help="Earthquake magnitude")
    parser.add_argument("--distance_km", type=float, default=45.0, help="Distance to epicenter in km")
    parser.add_argument("--seed", type=int, default=200, help="Base random seed")
    parser.add_argument("--output_dir", type=str, default=None, help="Output directory")
    args = parser.parse_args()

    run_ablation_study(
        trials_per_variant=args.trials,
        magnitude=args.magnitude,
        distance_km=args.distance_km,
        base_seed=args.seed,
        output_dir=args.output_dir
    )
