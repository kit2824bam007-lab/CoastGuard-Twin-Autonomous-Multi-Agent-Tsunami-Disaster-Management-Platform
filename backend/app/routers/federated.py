"""
API Router for V2 Extension 4 — Federated Learning Across Regional Twins
"""
from fastapi import APIRouter
from app.services.federated_learning import federated_learning_service

router = APIRouter(prefix="/api/federated", tags=["V2 — Federated Learning"])

@router.get("/status")
async def get_federated_status():
    return federated_learning_service.get_fl_status()

@router.post("/run-round")
async def run_federated_round():
    return federated_learning_service.run_federated_round()
