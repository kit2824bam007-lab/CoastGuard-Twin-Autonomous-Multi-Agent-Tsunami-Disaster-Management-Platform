"""
Reproduction script for historical paper results.
Executes the original ML classifier training and benchmark comparison logic
without modification to verify the reported paper figures.
Outputs reproducible verification metrics to console and JSON.
"""
import os
import sys
import json
import numpy as np

# Ensure backend root is on sys.path
backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from app.services.ml_classifier import MLHazardClassifier
from app.services.benchmark_service import BenchmarkService

def reproduce_ml_classifier():
    """Reproduces the Random Forest 4-class evaluation on 2,400 synthetic samples."""
    print("=" * 60)
    print("REPRODUCING ML HAZARD CLASSIFIER RESULTS")
    print("=" * 60)
    
    clf = MLHazardClassifier()
    metrics = clf.latest_metrics
    
    cm_raw = np.array(metrics["confusion_matrix_raw"])
    classes = metrics["classes"]
    
    # Calculate per-class metrics
    per_class = {}
    for i, c in enumerate(classes):
        tp = cm_raw[i, i]
        fn = cm_raw[i, :].sum() - tp
        fp = cm_raw[:, i].sum() - tp
        support = int(cm_raw[i, :].sum())
        prec = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
        rec = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        f1 = float(2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
        per_class[c] = {
            "support": support,
            "true_positive": int(tp),
            "false_negative": int(fn),
            "false_positive": int(fp),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4)
        }
    
    print(f"Total Dataset Samples: {metrics['dataset_samples']}")
    print(f"Test Samples: {metrics['test_samples']}")
    print(f"Accuracy: {metrics['accuracy'] * 100:.2f}%")
    print(f"Macro Precision: {metrics['precision'] * 100:.2f}%")
    print(f"Macro Recall: {metrics['recall'] * 100:.2f}%")
    print(f"Macro F1-Score: {metrics['f1_score'] * 100:.2f}%")
    print("\nConfusion Matrix (Raw Counts):")
    print("Actual \\ Predicted: " + "\t".join(classes))
    for i, c in enumerate(classes):
        print(f"{c:<12}: " + "\t\t".join(str(val) for val in cm_raw[i]))
    
    print("\nPer-Class Breakdown:")
    for c, data in per_class.items():
        print(f"  {c:<10}: Support={data['support']:<3} | Prec={data['precision']*100:5.1f}% | Rec={data['recall']*100:5.1f}% | F1={data['f1_score']*100:5.1f}%")
    
    return {
        "metrics": metrics,
        "per_class": per_class
    }

def reproduce_benchmark_metrics():
    """Reproduces the benchmark calculation for Magnitude 7.8, Distance 45km."""
    print("\n" + "=" * 60)
    print("REPRODUCING BENCHMARK COMPARISON (Mag 7.8, Dist 45km)")
    print("=" * 60)
    
    # We run 50 samples of the original service to establish the distribution of values
    # produced by its random.uniform generator around the base means.
    bench_service = BenchmarkService()
    
    samples = []
    for _ in range(50):
        res = bench_service._generate_benchmark_comparison(is_event_active=True, event_magnitude=7.8)
        sample_dict = {}
        for m in res["metrics"]:
            sample_dict[m["key"]] = {
                "baseline": m["baseline"],
                "proposed": m["proposed_swarm"],
                "improvement": m["improvement_percentage"]
            }
        samples.append(sample_dict)
        
    metric_keys = ["detection_time_sec", "avg_evac_time_min", "coverage_percentage", "path_success_rate"]
    summary = {}
    for k in metric_keys:
        base_vals = [s[k]["baseline"] for s in samples]
        prop_vals = [s[k]["proposed"] for s in samples]
        imp_vals = [s[k]["improvement"] for s in samples]
        summary[k] = {
            "baseline_mean": round(float(np.mean(base_vals)), 2),
            "baseline_range": [round(float(np.min(base_vals)), 2), round(float(np.max(base_vals)), 2)],
            "proposed_mean": round(float(np.mean(prop_vals)), 2),
            "proposed_range": [round(float(np.min(prop_vals)), 2), round(float(np.max(prop_vals)), 2)],
            "improvement_mean": round(float(np.mean(imp_vals)), 2),
            "improvement_range": [round(float(np.min(imp_vals)), 2), round(float(np.max(imp_vals)), 2)],
        }
        print(f"Metric: {k}")
        print(f"  Baseline: {summary[k]['baseline_mean']} (Range: {summary[k]['baseline_range']})")
        print(f"  Proposed: {summary[k]['proposed_mean']} (Range: {summary[k]['proposed_range']})")
        print(f"  Improvement: {summary[k]['improvement_mean']}% (Range: {summary[k]['improvement_range']}%)")
        
    return summary

def main():
    results_dir = os.path.join(backend_root, "..", "results", "reproduction")
    os.makedirs(results_dir, exist_ok=True)
    
    ml_res = reproduce_ml_classifier()
    bench_res = reproduce_benchmark_metrics()
    
    output = {
        "classifier_reproduction": ml_res,
        "benchmark_reproduction": bench_res
    }
    
    out_file = os.path.join(results_dir, "reproduction_summary.json")
    with open(out_file, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved reproduction output to {out_file}")

if __name__ == "__main__":
    main()
