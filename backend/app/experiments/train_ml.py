"""
Automated Model Training Script for CoastGuard Twin ML Hazard Classifier.
Supports:
1. Historical 2,400 synthetic dataset generation (for exact paper reproduction)
2. Calibrated physically consistent dataset generation with bounded noise
3. Stratified 70/15/15 train/val/test splitting with reproducible seed logging
4. Model artifact serialization and metadata recording to results/classifier/
"""
import os
import sys
import json
import argparse
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, balanced_accuracy_score, precision_recall_fscore_support, confusion_matrix

backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from app.services.ml_classifier import CLASSES, SHORELINE_MAP

def generate_dataset(num_samples: int = 2400, mode: str = "historical", seed: int = 42):
    """
    Generates synthetic dataset.
    mode='historical': Replicates original exponential distribution with threshold labels.
    mode='calibrated': Generates smooth physical probabilities with balanced class representation and sensor noise.
    """
    np.random.seed(seed)
    X = []
    y = []

    if mode == "historical":
        for _ in range(num_samples):
            p_wave = np.random.exponential(0.1)
            s_wave = np.random.exponential(0.2)
            buoy_anomaly = np.random.exponential(0.4)
            shoreline_code = np.random.choice([0, 1, 2], p=[0.7, 0.15, 0.15])
            max_inundation = max(0.0, buoy_anomaly * 1.5 - np.random.uniform(0.0, 1.0))
            distance_km = np.random.uniform(10.0, 200.0)

            if buoy_anomaly > 1.8 or max_inundation > 2.5 or (s_wave > 1.5 and shoreline_code == 2):
                label = 3 # SEVERE
            elif buoy_anomaly > 0.8 or max_inundation > 1.0 or s_wave > 0.8:
                label = 2 # WARNING
            elif buoy_anomaly > 0.3 or s_wave > 0.3 or shoreline_code == 1:
                label = 1 # WATCH
            else:
                label = 0 # NO_THREAT

            X.append([p_wave, s_wave, buoy_anomaly, shoreline_code, max_inundation, distance_km])
            y.append(label)

    elif mode == "calibrated":
        # Calibrated generation ensures sufficient support in high-severity classes
        # while adding realistic measurement noise to prevent trivial decision-tree memorization.
        for _ in range(num_samples):
            # Magnitude proxy
            mag = np.random.uniform(5.0, 9.2)
            dist = np.random.uniform(15.0, 180.0)
            
            # Physics scaling
            source_amp = (10 ** (mag - 6.0)) / np.sqrt(dist)
            p_wave = max(0.01, source_amp * 0.4 + np.random.normal(0, 0.05))
            s_wave = max(0.02, source_amp * 0.85 + np.random.normal(0, 0.08))
            
            # Buoy anomaly
            buoy_anomaly = max(-0.5, (10 ** (mag - 6.2)) * 0.8 / (dist ** 0.3) + np.random.normal(0, 0.15))
            
            # Shoreline state
            if buoy_anomaly > 1.5:
                shoreline_code = np.random.choice([1, 2], p=[0.2, 0.8])
            elif buoy_anomaly > 0.5:
                shoreline_code = np.random.choice([0, 1, 2], p=[0.2, 0.4, 0.4])
            else:
                shoreline_code = np.random.choice([0, 1], p=[0.85, 0.15])
                
            inundation = max(0.0, buoy_anomaly * 1.3 - 0.2 + np.random.normal(0, 0.1))
            
            # Probabilistic scoring rather than deterministic step functions
            score = 0.35 * (buoy_anomaly / 2.0) + 0.25 * (s_wave / 1.5) + 0.25 * (inundation / 3.0) + 0.15 * (shoreline_code / 2.0)
            noise_score = score + np.random.normal(0, 0.05)
            
            if noise_score > 0.70:
                label = 3 # SEVERE
            elif noise_score > 0.45:
                label = 2 # WARNING
            elif noise_score > 0.22:
                label = 1 # WATCH
            else:
                label = 0 # NO_THREAT
                
            X.append([p_wave, s_wave, buoy_anomaly, shoreline_code, inundation, dist])
            y.append(label)

    return np.array(X), np.array(y)

def train_classifier(num_samples: int = 2400, mode: str = "historical", seed: int = 42, output_dir: str = None):
    if output_dir is None:
        output_dir = os.path.join(backend_root, "..", "results", "classifier")
    os.makedirs(output_dir, exist_ok=True)

    print(f"Generating dataset ({mode} mode, N={num_samples}, seed={seed})...")
    X, y = generate_dataset(num_samples=num_samples, mode=mode, seed=seed)

    # 70% Train, 15% Val, 15% Test stratified
    X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.30, random_state=seed, stratify=y)
    X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.50, random_state=seed, stratify=y_temp)

    print(f"Dataset split: Train={len(X_train)}, Val={len(X_val)}, Test={len(X_test)}")
    
    # Train Random Forest
    clf = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=seed)
    clf.fit(X_train, y_train)

    # Evaluate on Validation set
    val_preds = clf.predict(X_val)
    val_acc = accuracy_score(y_val, val_preds)

    # Evaluate on Test set
    test_preds = clf.predict(X_test)
    test_acc = accuracy_score(y_test, test_preds)
    test_bal_acc = balanced_accuracy_score(y_test, test_preds)
    p_macro, r_macro, f1_macro, _ = precision_recall_fscore_support(y_test, test_preds, average='macro', zero_division=0)
    p_cls, r_cls, f1_cls, s_cls = precision_recall_fscore_support(y_test, test_preds, labels=[0, 1, 2, 3], zero_division=0)
    cm = confusion_matrix(y_test, test_preds, labels=[0, 1, 2, 3])

    # Save model
    model_filename = f"rf_classifier_{mode}_seed{seed}.joblib"
    model_path = os.path.join(output_dir, model_filename)
    joblib.dump(clf, model_path)

    # Compile report
    per_class = {}
    for i, name in enumerate(CLASSES):
        per_class[name] = {
            "support": int(s_cls[i]),
            "precision": round(float(p_cls[i]), 4),
            "recall": round(float(r_cls[i]), 4),
            "f1_score": round(float(f1_cls[i]), 4)
        }

    results = {
        "metadata": {
            "dataset_mode": mode,
            "num_samples": num_samples,
            "seed": seed,
            "train_samples": len(X_train),
            "val_samples": len(X_val),
            "test_samples": len(X_test),
            "features": ["p_wave", "s_wave", "buoy_anomaly", "shoreline_code", "max_inundation_m", "distance_km"],
            "classes": CLASSES
        },
        "validation_accuracy": round(float(val_acc), 4),
        "test_metrics": {
            "accuracy": round(float(test_acc), 4),
            "balanced_accuracy": round(float(test_bal_acc), 4),
            "macro_precision": round(float(p_macro), 4),
            "macro_recall": round(float(r_macro), 4),
            "macro_f1": round(float(f1_macro), 4),
            "per_class": per_class,
            "confusion_matrix": cm.tolist()
        }
    }

    metadata_path = os.path.join(output_dir, f"training_report_{mode}_seed{seed}.json")
    with open(metadata_path, "w") as f:
        json.dump(results, f, indent=2)

    print("\nTraining Complete.")
    print(f"Saved model artifact: {model_path}")
    print(f"Saved evaluation report: {metadata_path}")
    print(f"Test Accuracy: {test_acc*100:.2f}% | Balanced Accuracy: {test_bal_acc*100:.2f}% | Macro F1: {f1_macro*100:.2f}%")
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train CoastGuard Twin ML Hazard Classifier")
    parser.add_argument("--samples", type=int, default=2400, help="Number of synthetic samples")
    parser.add_argument("--mode", type=str, default="historical", choices=["historical", "calibrated"], help="Dataset generation mode")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output_dir", type=str, default=None, help="Output directory")
    args = parser.parse_args()

    train_classifier(num_samples=args.samples, mode=args.mode, seed=args.seed, output_dir=args.output_dir)
