"""
Tsunami risk prediction.

Two modes, same interface:
  - RuleBasedRiskModel  -> deployable TODAY, no training data needed (MVP / default)
  - MLRiskModel         -> trained on historical NOAA NGDC tsunami event data
                            (drop-in replacement once you have a trained model.pkl)

Both implement predict(features: dict) -> RiskPredictionResult
so the API layer never needs to know which one is active.
"""
import logging
from dataclasses import dataclass

logger = logging.getLogger("tsunami.risk_model")

from app.services.tectonic_plates import in_subduction_zone, distance_to_subduction_zone


@dataclass
class RiskPredictionResult:
    risk_level: str      # LOW / MODERATE / HIGH / SEVERE
    risk_score: float     # 0.0 - 1.0
    explanation: str
    model_version: str


class RuleBasedRiskModel:
    """
    Feature engineering + scoring logic:

      magnitude        -> primary driver (tsunamis are rare below M6.5)
      depth_km          -> shallow (<70km) quakes couple energy into water column far better
      is_offshore        -> tsunamis require underwater displacement
      in_high_risk_region -> historical subduction-zone base rate
      usgs_tsunami_flag  -> USGS's own real-time tsunami flag (huge signal if present)
      active_noaa_bulletin -> an active NOAA bulletin for the same basin

    Score is a weighted sum, clipped to [0,1], then bucketed into a risk_level.
    """
    version = "rule-based-v1"

    def predict(
        self,
        magnitude: float,
        depth_km: float,
        latitude: float,
        longitude: float,
        is_offshore: bool = True,
        usgs_tsunami_flag: bool = False,
        active_noaa_bulletin: bool = False,
    ) -> RiskPredictionResult:
        score = 0.0
        reasons = []

        # Magnitude — dominant factor (sigmoid-ish staircase)
        if magnitude >= 8.0:
            score += 0.45; reasons.append(f"M{magnitude:.1f} is a major/great earthquake")
        elif magnitude >= 7.0:
            score += 0.30; reasons.append(f"M{magnitude:.1f} is a strong earthquake")
        elif magnitude >= 6.5:
            score += 0.15; reasons.append(f"M{magnitude:.1f} exceeds the tsunami-relevant threshold")
        else:
            reasons.append(f"M{magnitude:.1f} below typical tsunamigenic threshold (6.5)")

        # Depth — shallow ruptures transfer more energy to the water column
        if depth_km <= 30:
            score += 0.20; reasons.append(f"very shallow rupture ({depth_km:.0f} km)")
        elif depth_km <= 70:
            score += 0.10; reasons.append(f"shallow rupture ({depth_km:.0f} km)")
        else:
            reasons.append(f"deep rupture ({depth_km:.0f} km) reduces surface coupling")

        # Offshore / underwater
        if is_offshore:
            score += 0.15; reasons.append("epicenter is offshore/underwater")
        else:
            score -= 0.10; reasons.append("epicenter is inland — tsunami unlikely")

        # Historical high-risk subduction zone
        if in_subduction_zone(longitude, latitude):
            zone, dist = distance_to_subduction_zone(longitude, latitude)
            score += 0.10; reasons.append(f"located near active subduction boundary ({zone}, d={dist:.0f}km)")

        # Real-time external signals
        if usgs_tsunami_flag:
            score += 0.20; reasons.append("USGS real-time feed flagged tsunami potential")
        if active_noaa_bulletin:
            score += 0.20; reasons.append("active NOAA tsunami bulletin for this basin")

        score = max(0.0, min(1.0, score))

        if score >= 0.75:
            level = "SEVERE"
        elif score >= 0.5:
            level = "HIGH"
        elif score >= 0.25:
            level = "MODERATE"
        else:
            level = "LOW"

        explanation = "; ".join(reasons)
        logger.info(f"Predicted {level} ({score:.2f}) — {explanation}")
        return RiskPredictionResult(
            risk_level=level,
            risk_score=round(score, 3),
            explanation=explanation,
            model_version=self.version,
        )


class MLRiskModel:
    """
    Drop-in ML replacement. Train offline (see /backend/train_model.py) on
    historical events from NOAA's NGDC/WDS Global Historical Tsunami Database:
        https://www.ngdc.noaa.gov/hazard/tsu_db.shtml
    Features: magnitude, depth_km, distance_to_coast_km, latitude, longitude,
              historical_region_frequency.
    Label: tsunami_generated (0/1) plus max_wave_height_m for severity.

    Loads a scikit-learn model saved via joblib (model.pkl). Falls back to
    the rule-based model automatically if no trained artifact is present —
    so the system is deployable before you ever train anything.
    """
    version = "ml-gradient-boost-v1"

    def __init__(self, model_path: str = "model.pkl"):
        self.model = None
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        path_options = [
            model_path,
            os.path.join(base_dir, model_path),
            os.path.join(os.getcwd(), model_path),
            os.path.join(os.getcwd(), "backend", model_path)
        ]
        for p in path_options:
            if os.path.exists(p):
                try:
                    import joblib
                    self.model = joblib.load(p)
                    logger.info(f"Loaded ML risk model from {p}")
                    break
                except Exception as e:
                    logger.warning(f"Failed loading model from {p}: {e}")
        if self.model is None:
            logger.info("No trained ML model found. Dynamically training RandomForest model...")
            try:
                from app.services.train_model import train_and_save_model
                train_and_save_model()
                # Retry loading
                for p in path_options:
                    if os.path.exists(p):
                        try:
                            import joblib
                            self.model = joblib.load(p)
                            logger.info(f"Dynamically trained and loaded ML risk model from {p}")
                            break
                        except Exception as loader_err:
                            logger.warning(f"Failed loading dynamically generated model from {p}: {loader_err}")
            except Exception as e:
                logger.error(f"Failed to dynamically train and load ML model: {e}")

        if self.model is None:
            logger.warning("No ML model available; system will fall back to RuleBasedRiskModel")

    def predict(self, magnitude, depth_km, latitude, longitude, is_offshore=True, **kwargs) -> RiskPredictionResult:
        if self.model is None:
            raise RuntimeError("ML model not loaded — fall back to RuleBasedRiskModel")
        import numpy as np
        X = np.array([[magnitude, depth_km, latitude, longitude, int(is_offshore)]])
        proba = self.model.predict_proba(X)[0][1]  # P(tsunami)
        level = "SEVERE" if proba >= 0.75 else "HIGH" if proba >= 0.5 else "MODERATE" if proba >= 0.25 else "LOW"
        return RiskPredictionResult(
            risk_level=level,
            risk_score=round(float(proba), 3),
            explanation=f"ML model probability of tsunami generation: {proba:.2%}",
            model_version=self.version,
        )


def get_active_risk_model():
    """Factory: try ML model, fall back to rule-based (safe default for deployment)."""
    ml = MLRiskModel()
    if ml.model is not None:
        return ml
    return RuleBasedRiskModel()
