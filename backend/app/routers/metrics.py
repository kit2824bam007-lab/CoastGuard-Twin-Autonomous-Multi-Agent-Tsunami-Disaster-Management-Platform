"""
API Router for Metrics Dashboard & Research Evaluation
"""
from fastapi import APIRouter
from app.services.ml_classifier import ml_classifier
from app.services.benchmark_service import benchmark_service
from app.services.data_sim_engine import sim_engine

router = APIRouter(prefix="/api/metrics", tags=["Metrics & Research Evaluation"])

@router.get("/classifier")
async def get_classifier_metrics():
    """Returns ML hazard model performance metrics and confusion matrix (paper Fig 5)."""
    return ml_classifier.latest_metrics

@router.get("/benchmark")
async def get_benchmark_comparison():
    """Returns Centralized Baseline vs Proposed Swarm Digital Twin evaluation (paper Table 1 / Fig 7)."""
    snapshot = sim_engine.get_latest_snapshot()
    is_active = snapshot["is_event_active"]
    mag = snapshot["event_params"]["magnitude"]
    return benchmark_service.run_live_comparison(is_event_active=is_active, event_magnitude=mag)
