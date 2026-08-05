"""
API Router for Layer 3 — Swarm Intelligence Coordination
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, List
from app.services.swarm_engine import swarm_engine

router = APIRouter(prefix="/api/swarm", tags=["Layer 3 — Swarm Intelligence"])

class DeployAgentRequest(BaseModel):
    agent_type: str = Field(default="UAV", description="Agent type: UAV, USV, or GROUND")
    x: float = Field(default=20.0, ge=0.0, le=49.0)
    y: float = Field(default=20.0, ge=0.0, le=49.0)

class SimulateLossRequest(BaseModel):
    agent_id: str = Field(..., description="ID of agent to disconnect/disable e.g. UAV-101")

class ReassignCoverageRequest(BaseModel):
    sector_name: str = Field(default="Sector-1")
    target_x: float = Field(..., ge=0.0, le=49.0)
    target_y: float = Field(..., ge=0.0, le=49.0)

@router.get("/agents")
async def get_swarm_agents():
    return {
        "agents": [a.to_dict() for a in swarm_engine.agents.values()]
    }

@router.get("/topology")
async def get_mesh_topology():
    return swarm_engine.update_mesh_topology()

@router.post("/deploy")
async def deploy_agent(req: DeployAgentRequest):
    if req.agent_type.upper() not in ["UAV", "USV", "GROUND"]:
        raise HTTPException(status_code=400, detail="Invalid agent type. Must be UAV, USV, or GROUND.")
    
    agent = swarm_engine.deploy_agent(req.agent_type.upper(), req.x, req.y)
    return {
        "status": "DEPLOYED",
        "agent": agent.to_dict()
    }

@router.post("/simulate-loss")
async def simulate_agent_loss(req: SimulateLossRequest):
    if req.agent_id not in swarm_engine.agents:
        raise HTTPException(status_code=4404, detail=f"Agent '{req.agent_id}' not found.")
    
    swarm_engine.simulate_agent_loss(req.agent_id)
    return {
        "status": "AGENT_LOST_SIMULATED",
        "agent_id": req.agent_id,
        "message": f"Agent {req.agent_id} connectivity dropped. Mesh topology auto-adjusting.",
        "topology": swarm_engine.update_mesh_topology()
    }

@router.post("/toggle-satellite")
async def toggle_satellite_failover():
    active = swarm_engine.toggle_satellite_failover()
    return {
        "status": "SATELLITE_FAILOVER_TOGGLED",
        "is_satellite_failover_active": active,
        "message": f"LEO Satellite comms failover {'ACTIVATED' if active else 'DEACTIVATED'}."
    }

@router.post("/reassign")
async def reassign_coverage(req: ReassignCoverageRequest):
    swarm_engine.reassign_coverage(req.sector_name, req.target_x, req.target_y)
    return {
        "status": "COVERAGE_REASSIGNED",
        "sector": req.sector_name,
        "target": {"x": req.target_x, "y": req.target_y}
    }
