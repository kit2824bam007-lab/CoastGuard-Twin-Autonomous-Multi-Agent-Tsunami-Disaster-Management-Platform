"""
Independent Statistical Analysis Script for CoastGuard Twin Experiments
Reads raw trial-level records, recalculates all reported metrics, computes:
- Mean and Standard Deviation
- Median and Interquartile Range (IQR)
- 95% Confidence Intervals
- Paired differences between methods
- Effect size (Cohen's d)
- Paired Student's t-test and Wilcoxon signed-rank test
- Formatted CSV and JSON summaries in results/processed/
"""
import os
import sys
import csv
import json
import argparse
import numpy as np
import scipy.stats as stats

backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

def compute_cohens_d(x, y):
    """Computes paired Cohen's d effect size."""
    diff = np.array(x) - np.array(y)
    n = len(diff)
    if n < 2:
        return 0.0
    s_diff = np.std(diff, ddof=1)
    return float(np.mean(diff) / s_diff) if s_diff > 0 else 0.0

def extract_val(record, primary_key, fallback_keys):
    if primary_key in record and record[primary_key] != "":
        return float(record[primary_key])
    for fk in fallback_keys:
        if fk in record and record[fk] != "":
            return float(record[fk])
    raise KeyError(f"Metric '{primary_key}' not found in record (checked fallbacks: {fallback_keys})")

def analyze_raw_benchmark_data(raw_csv_path: str = None, output_dir: str = None):
    results_root = os.path.join(backend_root, "..", "results")
    if raw_csv_path is None:
        # Check raw/ first, then benchmark/
        for cdir in [os.path.join(results_root, "raw"), os.path.join(results_root, "benchmark")]:
            if os.path.exists(cdir):
                csv_files = [f for f in os.listdir(cdir) if f.startswith("raw_trials") and f.endswith(".csv")]
                if csv_files:
                    if "raw_trials_m7.8_d45.0_n30.csv" in csv_files:
                        raw_csv_path = os.path.join(cdir, "raw_trials_m7.8_d45.0_n30.csv")
                    else:
                        csv_files.sort()
                        raw_csv_path = os.path.join(cdir, csv_files[-1])
                    break
        if raw_csv_path is None:
            raise FileNotFoundError("No raw trial CSV found in results/raw or results/benchmark")

    if output_dir is None:
        output_dir = os.path.join(results_root, "processed")
    os.makedirs(output_dir, exist_ok=True)

    print(f"Loading raw trial data from: {raw_csv_path}")

    baseline_records = []
    proposed_records = []

    with open(raw_csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if "Baseline" in row["Architecture"]:
                baseline_records.append(row)
            else:
                proposed_records.append(row)

    print(f"Loaded {len(baseline_records)} Baseline trials and {len(proposed_records)} Proposed Swarm trials.")
    assert len(baseline_records) == len(proposed_records), "Mismatch in paired trial counts!"

    metric_keys = [
        ("Detection_To_Alert_Time_s", "Detection-to-Alert Time", "seconds", True, ["detection_to_alert_time_sec"]),
        ("Evacuation_Duration_min", "Evacuation Transit Duration", "minutes", True, ["Evacuation_Time_min", "evacuation_time_min"]),
        ("Total_Response_Time_min", "Total Emergency Response Time", "minutes", True, ["total_response_time_min"]),
        ("Search_Coverage_pct", "Search-Area Coverage", "%", False, ["search_coverage_pct"]),
        ("Path_Planning_Success_pct", "Path-Planning Success Rate", "%", False, ["path_planning_success_pct"]),
        ("Evacuation_Completion_pct", "Civilian Evacuation Survival", "%", False, ["Evacuation_Success_pct", "evacuation_success_rate_pct"])
    ]

    analysis_results = []

    for col_key, title, unit, lower_is_better, fallbacks in metric_keys:
        b_vals = np.array([extract_val(r, col_key, fallbacks) for r in baseline_records])
        p_vals = np.array([extract_val(r, col_key, fallbacks) for r in proposed_records])
        diff = p_vals - b_vals

        n = len(b_vals)
        b_mean = float(np.mean(b_vals))
        b_std = float(np.std(b_vals, ddof=1)) if n > 1 else 0.0
        b_med = float(np.median(b_vals))
        b_iqr = float(stats.iqr(b_vals))
        b_ci = 1.96 * (b_std / np.sqrt(n)) if n > 0 else 0.0

        p_mean = float(np.mean(p_vals))
        p_std = float(np.std(p_vals, ddof=1)) if n > 1 else 0.0
        p_med = float(np.median(p_vals))
        p_iqr = float(stats.iqr(p_vals))
        p_ci = 1.96 * (p_std / np.sqrt(n)) if n > 0 else 0.0

        diff_mean = float(np.mean(diff))
        diff_std = float(np.std(diff, ddof=1)) if n > 1 else 0.0

        # Percentage improvement
        if lower_is_better:
            rel_imp = ((b_mean - p_mean) / b_mean) * 100.0 if b_mean > 0 else 0.0
        else:
            rel_imp = ((p_mean - b_mean) / b_mean) * 100.0 if b_mean > 0 else 0.0

        cohens_d = compute_cohens_d(p_vals, b_vals)

        # Statistical hypothesis testing
        # 1. Paired Student's t-test
        t_stat, t_pval = stats.ttest_rel(p_vals, b_vals)
        
        # 2. Wilcoxon signed-rank test
        # Handle zero-variance / zero-difference cases gracefully
        if np.all(diff == 0):
            w_stat, w_pval = 0.0, 1.0
        else:
            try:
                w_stat, w_pval = stats.wilcoxon(p_vals, b_vals)
            except ValueError:
                w_stat, w_pval = 0.0, 1.0

        analysis_results.append({
            "metric_key": col_key,
            "title": title,
            "unit": unit,
            "lower_is_better": lower_is_better,
            "sample_size_n": n,
            "baseline": {
                "mean": round(b_mean, 2),
                "std": round(b_std, 2),
                "median": round(b_med, 2),
                "iqr": round(b_iqr, 2),
                "ci95": [round(b_mean - b_ci, 2), round(b_mean + b_ci, 2)]
            },
            "proposed_swarm": {
                "mean": round(p_mean, 2),
                "std": round(p_std, 2),
                "median": round(p_med, 2),
                "iqr": round(p_iqr, 2),
                "ci95": [round(p_mean - p_ci, 2), round(p_mean + p_ci, 2)]
            },
            "paired_difference": {
                "mean_diff": round(diff_mean, 2),
                "std_diff": round(diff_std, 2),
                "relative_improvement_pct": round(rel_imp, 1),
                "cohens_d": round(cohens_d, 2)
            },
            "hypothesis_tests": {
                "t_statistic": round(float(t_stat), 2) if not np.isnan(t_stat) else 0.0,
                "t_p_value": float(t_pval) if not np.isnan(t_pval) else 1.0,
                "wilcoxon_statistic": round(float(w_stat), 2) if not np.isnan(w_stat) else 0.0,
                "wilcoxon_p_value": float(w_pval) if not np.isnan(w_pval) else 1.0,
                "statistically_significant_001": bool(t_pval < 0.01) if not np.isnan(t_pval) else False
            }
        })

    # Save to JSON
    json_path = os.path.join(output_dir, "statistical_analysis_report.json")
    with open(json_path, "w") as f:
        json.dump({
            "source_file": os.path.basename(raw_csv_path),
            "num_paired_trials": len(baseline_records),
            "metrics": analysis_results
        }, f, indent=2)

    # Save to CSV table
    csv_path = os.path.join(output_dir, "statistical_summary_table.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Metric", "Unit", "Baseline_Mean_Std", "Baseline_Median_IQR", "Baseline_95CI",
            "Swarm_Mean_Std", "Swarm_Median_IQR", "Swarm_95CI",
            "Rel_Improvement_pct", "Cohens_d", "t_Stat", "p_Value_t", "Wilcoxon_p_Value", "Sig_001"
        ])
        for r in analysis_results:
            b = r["baseline"]
            p = r["proposed_swarm"]
            d = r["paired_difference"]
            h = r["hypothesis_tests"]
            writer.writerow([
                r["title"], r["unit"],
                f"{b['mean']} ± {b['std']}", f"{b['median']} ({b['iqr']})", f"[{b['ci95'][0]}, {b['ci95'][1]}]",
                f"{p['mean']} ± {p['std']}", f"{p['median']} ({p['iqr']})", f"[{p['ci95'][0]}, {p['ci95'][1]}]",
                f"{d['relative_improvement_pct']}%", d["cohens_d"],
                h["t_statistic"], f"{h['t_p_value']:.4e}", f"{h['wilcoxon_p_value']:.4e}",
                "YES" if h["statistically_significant_001"] else "NO"
            ])

    print("\n" + "=" * 95)
    print(f"{'Metric':<28} | {'Baseline (Mean ± Std)':<22} | {'Swarm (Mean ± Std)':<20} | {'Imp (%)':<8} | {'p-value':<10}")
    print("=" * 95)
    for r in analysis_results:
        b_str = f"{r['baseline']['mean']} ± {r['baseline']['std']} {r['unit']}"
        p_str = f"{r['proposed_swarm']['mean']} ± {r['proposed_swarm']['std']} {r['unit']}"
        imp_str = f"{r['paired_difference']['relative_improvement_pct']}%"
        pval = r['hypothesis_tests']['t_p_value']
        pval_str = "< 0.0001" if pval < 0.0001 else f"{pval:.4f}"
        print(f"{r['title']:<28} | {b_str:<22} | {p_str:<20} | {imp_str:<8} | {pval_str:<10}")
    print("=" * 95)
    print(f"\nStatistical JSON saved to: {json_path}")
    print(f"Summary Table CSV saved to: {csv_path}")

    return analysis_results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Statistical Analysis of CoastGuard Twin Benchmark Records")
    parser.add_argument("--input", type=str, default=None, help="Path to raw trial CSV")
    parser.add_argument("--output_dir", type=str, default=None, help="Output directory for processed statistics")
    args = parser.parse_args()

    analyze_raw_benchmark_data(raw_csv_path=args.input, output_dir=args.output_dir)
