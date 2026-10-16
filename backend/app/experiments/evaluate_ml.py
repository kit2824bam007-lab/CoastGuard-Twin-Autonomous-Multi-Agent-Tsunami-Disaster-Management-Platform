"""
Automated Model Evaluation Script for CoastGuard Twin ML Hazard Classifier.
Evaluates model performance across:
1. Standard test split
2. Noise robustness stress testing (evaluating performance degradation under sensor noise)
Exports CSV and JSON metrics into results/classifier/
"""
import os
import sys
import csv
import json
import argparse
import joblib
import numpy as np
from sklearn.metrics import accuracy_score, balanced_accuracy_score, precision_recall_fscore_support, confusion_matrix

backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from app.services.ml_classifier import CLASSES
from app.experiments.train_ml import generate_dataset, train_test_split

def evaluate_model(model_path: str = None, mode: str = "historical", num_samples: int = 2400, seed: int = 42, output_dir: str = None):
    if output_dir is None:
        output_dir = os.path.join(backend_root, "..", "results", "classifier")
    os.makedirs(output_dir, exist_ok=True)

    # If model_path is not specified, check default or train one
    if model_path is None or not os.path.exists(model_path):
        candidate = os.path.join(output_dir, f"rf_classifier_{mode}_seed{seed}.joblib")
        if os.path.exists(candidate):
            model_path = candidate
        else:
            print(f"Model artifact not found at {candidate}. Training temporary model...")
            from app.experiments.train_ml import train_classifier
            train_classifier(num_samples=num_samples, mode=mode, seed=seed, output_dir=output_dir)
            model_path = candidate

    print(f"Loading model artifact from {model_path}...")
    clf = joblib.load(model_path)

    # Generate held-out test data
    X, y = generate_dataset(num_samples=num_samples, mode=mode, seed=seed)
    _, X_temp, _, y_temp = train_test_split(X, y, test_size=0.30, random_state=seed, stratify=y)
    _, X_test, _, y_test = train_test_split(X_temp, y_temp, test_size=0.50, random_state=seed, stratify=y_temp)

    # Baseline evaluation
    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    bal_acc = balanced_accuracy_score(y_test, y_pred)
    p_macro, r_macro, f1_macro, _ = precision_recall_fscore_support(y_test, y_pred, average='macro', zero_division=0)
    p_cls, r_cls, f1_cls, s_cls = precision_recall_fscore_support(y_test, y_pred, labels=[0, 1, 2, 3], zero_division=0)
    cm = confusion_matrix(y_test, y_pred, labels=[0, 1, 2, 3])

    # Stress testing: Sensor noise perturbation
    noise_levels = [0.0, 0.05, 0.10, 0.20, 0.30]
    stress_results = []
    
    for noise_std in noise_levels:
        if noise_std == 0.0:
            X_noisy = X_test.copy()
        else:
            np.random.seed(seed)
            noise = np.random.normal(0, noise_std, size=X_test.shape)
            # Only add noise to continuous features (indices 0, 1, 2, 4, 5)
            noise[:, 3] = 0.0
            X_noisy = np.maximum(0.0, X_test + noise)
            
        preds_noisy = clf.predict(X_noisy)
        acc_noisy = accuracy_score(y_test, preds_noisy)
        bal_acc_noisy = balanced_accuracy_score(y_test, preds_noisy)
        _, _, f1_noisy, _ = precision_recall_fscore_support(y_test, preds_noisy, average='macro', zero_division=0)
        stress_results.append({
            "noise_level_sigma": noise_std,
            "accuracy": round(float(acc_noisy), 4),
            "balanced_accuracy": round(float(bal_acc_noisy), 4),
            "macro_f1": round(float(f1_noisy), 4)
        })

    # Export Per-Class CSV
    csv_path = os.path.join(output_dir, f"evaluation_metrics_{mode}_seed{seed}.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Class_Name", "Class_Index", "Support", "Precision", "Recall", "F1_Score"])
        for i, cname in enumerate(CLASSES):
            writer.writerow([cname, i, int(s_cls[i]), round(float(p_cls[i]), 4), round(float(r_cls[i]), 4), round(float(f1_cls[i]), 4)])
        writer.writerow([])
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Overall Accuracy", round(float(acc), 4)])
        writer.writerow(["Balanced Accuracy", round(float(bal_acc), 4)])
        writer.writerow(["Macro Precision", round(float(p_macro), 4)])
        writer.writerow(["Macro Recall", round(float(r_macro), 4)])
        writer.writerow(["Macro F1", round(float(f1_macro), 4)])

    # Export JSON
    eval_json_path = os.path.join(output_dir, f"evaluation_summary_{mode}_seed{seed}.json")
    summary = {
        "model_file": os.path.basename(model_path),
        "dataset_mode": mode,
        "seed": seed,
        "test_sample_count": len(X_test),
        "overall_accuracy": round(float(acc), 4),
        "balanced_accuracy": round(float(bal_acc), 4),
        "macro_precision": round(float(p_macro), 4),
        "macro_recall": round(float(r_macro), 4),
        "macro_f1": round(float(f1_macro), 4),
        "per_class": {
            CLASSES[i]: {
                "support": int(s_cls[i]),
                "precision": round(float(p_cls[i]), 4),
                "recall": round(float(r_cls[i]), 4),
                "f1_score": round(float(f1_cls[i]), 4)
            } for i in range(4)
        },
        "confusion_matrix_raw": cm.tolist(),
        "noise_stress_testing": stress_results
    }
    with open(eval_json_path, "w") as f:
        json.dump(summary, f, indent=2)

    print("\nEvaluation Summary:")
    print(f"Overall Accuracy:  {acc*100:.2f}%")
    print(f"Balanced Accuracy: {bal_acc*100:.2f}%")
    print(f"Macro F1-Score:    {f1_macro*100:.2f}%")
    print("\nPer-Class Breakdown:")
    for i, cname in enumerate(CLASSES):
        print(f"  {cname:<10}: Support={s_cls[i]:<3} | Prec={p_cls[i]*100:5.1f}% | Rec={r_cls[i]*100:5.1f}% | F1={f1_cls[i]*100:5.1f}%")
    print(f"\nSaved CSV: {csv_path}")
    print(f"Saved JSON: {eval_json_path}")

    return summary

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate CoastGuard Twin ML Hazard Classifier")
    parser.add_argument("--model_path", type=str, default=None, help="Path to .joblib model")
    parser.add_argument("--mode", type=str, default="historical", choices=["historical", "calibrated"], help="Dataset generation mode")
    parser.add_argument("--samples", type=int, default=2400, help="Number of synthetic samples")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output_dir", type=str, default=None, help="Output directory")
    args = parser.parse_args()

    evaluate_model(model_path=args.model_path, mode=args.mode, num_samples=args.samples, seed=args.seed, output_dir=args.output_dir)
