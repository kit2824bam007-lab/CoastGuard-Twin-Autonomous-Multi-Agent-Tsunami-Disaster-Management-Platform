"""
Scenario Configuration Module for CoastGuard Twin Simulation Experiments
Stores scenario parameters independently from algorithm implementations.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass
class ScenarioConfig:
    scenario_id: str
    name: str
    description: str
    magnitude: float
    distance_km: float
    grid_size: int = 50
    num_civilians: int = 40
    sim_duration_steps: int = 150
    step_duration_sec: float = 2.0
    safe_shelter_x: float = 46.0
    safe_shelter_y: float = 25.0
    comm_range: float = 12.0
    enable_agent_failure: bool = True
    failed_agent_step: int = 40
    failed_agent_id: str = "UAV-101"
    packet_loss_rate: float = 0.0 # 0.0 = ideal, 0.3 = 30% loss
    extra_params: Dict[str, Any] = field(default_factory=dict)

# Standardized benchmark scenario catalog
SCENARIO_CATALOG: Dict[str, ScenarioConfig] = {
    "SCENARIO_M78_D45": ScenarioConfig(
        scenario_id="SCENARIO_M78_D45",
        name="Benchmark Coastal Scenario (M7.8, 45km)",
        description="Standard IEEE evaluation scenario with M7.8 offshore rupture at 45km from coastline.",
        magnitude=7.8,
        distance_km=45.0,
        num_civilians=40,
        sim_duration_steps=150
    ),
    "SCENARIO_M85_D30": ScenarioConfig(
        scenario_id="SCENARIO_M85_D30",
        name="Megathrust Nearshore Scenario (M8.5, 30km)",
        description="Severe nearshore rupture with rapid arrival (<60s) and large runup elevation.",
        magnitude=8.5,
        distance_km=30.0,
        num_civilians=60,
        sim_duration_steps=180
    ),
    "SCENARIO_M68_D90": ScenarioConfig(
        scenario_id="SCENARIO_M68_D90",
        name="Moderate Distant Event (M6.8, 90km)",
        description="Moderate offshore event with slower arrival and lower surge amplitudes.",
        magnitude=6.8,
        distance_km=90.0,
        num_civilians=30,
        sim_duration_steps=150
    ),
    "SCENARIO_COMM_STRESS": ScenarioConfig(
        scenario_id="SCENARIO_COMM_STRESS",
        name="Ad-Hoc Network Degradation (M7.8, 40% Packet Loss)",
        description="Standard M7.8 event under degraded RF mesh communications with 40% packet loss.",
        magnitude=7.8,
        distance_km=45.0,
        num_civilians=40,
        sim_duration_steps=150,
        packet_loss_rate=0.40
    )
}

def get_scenario(scenario_id: str = "SCENARIO_M78_D45") -> ScenarioConfig:
    return SCENARIO_CATALOG.get(scenario_id, SCENARIO_CATALOG["SCENARIO_M78_D45"])
