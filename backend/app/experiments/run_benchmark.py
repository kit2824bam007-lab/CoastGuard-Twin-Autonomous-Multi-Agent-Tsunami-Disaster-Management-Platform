"""
Multi-Trial Simulation Benchmark Runner for CoastGuard Twin
Executes N independently seeded simulation trials under equivalent scenario conditions
comparing Centralized Baseline vs. Proposed Multi-Agent Swarm System.
Calculates Mean, Standard Deviation, and 95% Confidence Intervals.
Exports raw trial CSVs and statistical JSON summaries to results/benchmark/ and results/raw/
"""
import os
import sys
import csv
import json
import argparse
import numpy as np

backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from app.services.simulation_benchmark_runner import BenchmarkRunner

def run_multi_trial_benchmark(
    num_trials: int = 30,
    magnitude: float = 7.8,
    distance_km: float = 45.0,
    base_seed: int = 100,
    output_dir: str = None
):
    if output_dir is None:
        output_dir = os.path.join(backend_root, "..", "results", "benchmark")
    raw_dir = os.path.join(backend_root, "..", "results", "raw")
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(raw_dir, exist_ok=True)

    print("=" * 70)
    print(f"RUNNING MULTI-TRIAL SIMULATION BENCHMARK (N={num_trials} Trials)")
    print(f"Scenario: Magnitude {magnitude}, Epicenter Distance {distance_km} km")
    print("=" * 70)

    runner = BenchmarkRunner(num_trials=num_trials, base_seed=base_seed)
    results = runner.run_benchmark(magnitude=magnitude, distance_km=distance_km)

    csv_headers = [
        "Trial_ID", "Seed", "Architecture",
        "Observation_Time_s", "Decision_Time_s", "Transmission_Time_s", "Alert_Dispatch_Time_s",
        "Detection_To_Alert_Time_s", "Evacuation_Duration_s", "Evacuation_Duration_min",
        "Total_Response_Time_s", "Total_Response_Time_min", "Evacuation_Completion_pct",
        "Search_Coverage_pct", "Path_Planning_Success_pct", "Civilians_Evacuated",
        "Civilians_Trapped", "Civilians_In_Transit", "Total_Civilians",
        "Communication_Messages", "Execution_Duration_ms"
    ]

    def trial_to_row(t):
        return [
            t["trial_id"], t["seed"], t["architecture"],
            t["observation_time_sec"], t["decision_time_sec"], t["transmission_time_sec"],
            t["alert_dispatch_time_sec"], t["detection_to_alert_time_sec"],
            t["evacuation_duration_sec"], t["evacuation_duration_min"],
            t["total_response_time_sec"], t["total_response_time_min"],
            t["evacuation_completion_pct"], t["search_coverage_pct"],
            t["path_planning_success_pct"], t["civilians_evacuated"],
            t["civilians_trapped"], t["civilians_in_transit"], t["total_civilians"],
            t["communication_messages"], t["execution_duration_ms"]
        ]

    # 1. Export Raw Trials CSV to benchmark/ and raw/
    raw_csv_filename = f"raw_trials_m{magnitude}_d{distance_km}_n{num_trials}.csv"
    for target_dir in [output_dir, raw_dir]:
        raw_csv_path = os.path.join(target_dir, raw_csv_filename)
        with open(raw_csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(csv_headers)
            for t in results["raw_trials"]["baseline"]:
                writer.writerow(trial_to_row(t))
            for t in results["raw_trials"]["proposed_swarm"]:
                writer.writerow(trial_to_row(t))

    # 2. Export Aggregate Summary CSV
    summary_csv_path = os.path.join(output_dir, f"summary_metrics_m{magnitude}_d{distance_km}_n{num_trials}.csv")
    with open(summary_csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Metric", "Unit", "Baseline_Mean", "Baseline_Std", "Baseline_95CI_Low", "Baseline_95CI_High",
            "Proposed_Mean", "Proposed_Std", "Proposed_95CI_Low", "Proposed_95CI_High",
            "Improvement_Percentage", "Preferred_Direction"
        ])
        for m in results["comparison_metrics"]:
            writer.writerow([
                m["title"], m["unit"],
                m["baseline_mean"], m["baseline_std"], m["baseline_ci95"][0], m["baseline_ci95"][1],
                m["proposed_mean"], m["proposed_std"], m["proposed_ci95"][0], m["proposed_ci95"][1],
                m["improvement_percentage"], "Lower is Better" if m["lower_is_better"] else "Higher is Better"
            ])

    # 3. Export Full JSON with metadata
    json_path = os.path.join(output_dir, f"benchmark_full_report_m{magnitude}_d{distance_km}_n{num_trials}.json")
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2)

    # Print clean summary table
    print("\nBENCHMARK STATISTICAL SUMMARY:")
    print("-" * 75)
    print(f"{'Metric':<30} | {'Baseline (Mean ± Std)':<22} | {'Proposed Swarm':<20} | {'Improvement':<12}")
    print("-" * 75)
    for m in results["comparison_metrics"]:
        b_str = f"{m['baseline_mean']} ± {m['baseline_std']} {m['unit']}"
        p_str = f"{m['proposed_mean']} ± {m['proposed_std']} {m['unit']}"
        imp_str = f"{'+' if not m['lower_is_better'] else '-'}{abs(m['improvement_percentage'])}%"
        print(f"{m['title']:<30} | {b_str:<22} | {p_str:<20} | {imp_str:<12}")
    print("-" * 75)
    print(f"\nSaved Raw Trials CSV:   {os.path.join(raw_dir, raw_csv_filename)}")
    print(f"Saved Summary CSV:      {summary_csv_path}")
    print(f"Saved Full JSON Report: {json_path}")

    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run CoastGuard Twin Simulation Benchmark")
    parser.add_argument("--trials", type=int, default=30, help="Number of simulation trials per architecture")
    parser.add_argument("--magnitude", type=float, default=7.8, help="Earthquake magnitude")
    parser.add_argument("--distance_km", type=float, default=45.0, help="Distance to epicenter in km")
    parser.add_argument("--seed", type=int, default=100, help="Base random seed")
    parser.add_argument("--output_dir", type=str, default=None, help="Output directory")
    args = parser.parse_args()

    run_multi_trial_benchmark(
        num_trials=args.trials,
        magnitude=args.magnitude,
        distance_km=args.distance_km,
        base_seed=args.seed,
        output_dir=args.output_dir
    )
