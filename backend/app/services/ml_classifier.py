"""
Layer 5 — Machine Learning Hazard Classifier & Severity Scoring Engine
Implements:
1. RandomForest Hazard Classifier trained on synthetic data (70/15/15 train/val/test split)
2. Live accuracy, precision, recall, F1 evaluation and 4x4 confusion matrix generator (matching paper Fig 5)
3. AlertChannel abstraction hierarchy
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix

CLASSES = ["NO_THREAT", "WATCH", "WARNING", "SEVERE"]
SHORELINE_MAP = {"NORMAL": 0, "RECEDING": 1, "SURGING": 2}

class MLHazardClassifier:
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.is_trained = False
        self.latest_metrics: Dict[str, Any] = {}
        self._train_initial_model()

    def _generate_synthetic_dataset(self, num_samples: int = 2000) -> Tuple[np.ndarray, np.ndarray]:
        """Generates realistic synthetic tsunami hazard dataset."""
        np.random.seed(42)
        
        # Features: [p_wave, s_wave, buoy_anomaly, shoreline_code, max_inundation_m, distance_km]
        X = []
        y = []

        for _ in range(num_samples):
            # Sample random operational & scenario conditions
            p_wave = np.random.exponential(0.1)
            s_wave = np.random.exponential(0.2)
            buoy_anomaly = np.random.exponential(0.4)
            shoreline_code = np.random.choice([0, 1, 2], p=[0.7, 0.15, 0.15])
            max_inundation = max(0.0, buoy_anomaly * 1.5 - np.random.uniform(0.0, 1.0))
            distance_km = np.random.uniform(10.0, 200.0)

            # Heuristic ground truth target assignment
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

        return np.array(X), np.array(y)

    def _train_initial_model(self):
        """Trains model with 70/15/15 train/val/test split matching research paper methodology."""
        X, y = self._generate_synthetic_dataset(2400)

        # 70% Train, 30% Temp (15% Val, 15% Test)
        X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.30, random_state=42, stratify=y)
        X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.50, random_state=42, stratify=y_temp)

        # Fit model on training set
        self.model.fit(X_train, y_train)

        # Evaluate on test set
        y_pred = self.model.predict(X_test)
        
        acc = accuracy_score(y_test, y_pred)
        precision, recall, f1, _ = precision_recall_fscore_support(y_test, y_pred, average='macro')
        cm = confusion_matrix(y_test, y_pred, labels=[0, 1, 2, 3])

        # Normalize confusion matrix to percentages for clean display
        cm_norm = np.round(cm.astype('float') / cm.sum(axis=1)[:, np.newaxis] * 100, 1).tolist()

        self.latest_metrics = {
            "dataset_samples": len(X),
            "train_samples": len(X_train),
            "val_samples": len(X_val),
            "test_samples": len(X_test),
            "accuracy": round(float(acc), 4),
            "precision": round(float(precision), 4),
            "recall": round(float(recall), 4),
            "f1_score": round(float(f1), 4),
            "classes": CLASSES,
            "confusion_matrix_raw": cm.tolist(),
            "confusion_matrix_percentage": cm_norm
        }
        self.is_trained = True

    def predict(self, p_wave: float, s_wave: float, buoy_anomaly: float, shoreline_state: str, max_inundation: float, distance_km: float) -> Dict[str, Any]:
        """Classifies live fused sensor features into 4-class hazard severity."""
        if not self.is_trained:
            self._train_initial_model()

        shore_code = SHORELINE_MAP.get(shoreline_state, 0)
        sample = np.array([[p_wave, s_wave, buoy_anomaly, shore_code, max_inundation, distance_km]])
        
        pred_class_idx = int(self.model.predict(sample)[0])
        probabilities = self.model.predict_proba(sample)[0].tolist()

        return {
            "predicted_class": CLASSES[pred_class_idx],
            "severity_index": pred_class_idx,
            "confidence": round(float(probabilities[pred_class_idx]), 3),
            "class_probabilities": {CLASSES[i]: round(float(probabilities[i]), 3) for i in range(len(CLASSES))}
        }

# Abstract Alert Channel Stub
class AlertChannel:
    def dispatch(self, title: str, message: str, severity: str) -> Dict[str, Any]:
        raise NotImplementedError

class ConsoleAlertChannel(AlertChannel):
    def dispatch(self, title: str, message: str, severity: str) -> Dict[str, Any]:
        print(f"[ALERT DISPATCH - {severity.upper()}] {title}: {message}")
        return {"channel": "console", "status": "DISPATCHED", "title": title, "severity": severity}

class WebSocketAlertChannel(AlertChannel):
    def dispatch(self, title: str, message: str, severity: str) -> Dict[str, Any]:
        return {"channel": "websocket", "status": "BROADCAST", "title": title, "severity": severity}

ml_classifier = MLHazardClassifier()
