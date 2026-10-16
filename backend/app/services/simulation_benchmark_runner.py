"""
Simulation Benchmark & Ablation Engine for CoastGuard Twin
Provides:
1. End-to-end discrete-event coastal disaster simulation over 50x50 bathymetry grid
2. Direct comparison between Centralized Baseline and Proposed Multi-Agent Swarm
3. Heterogeneous Swarm dynamics (UAV, USV, GROUND) with PSO + A* Path Planning
4. Dynamic Civilian Population Evacuation Simulation toward highland shelter
5. Component Ablation Experiments (No-PSO, No-A*, No-Mesh, Centralized)
6. Explicit timestamp tracking: observation, decision, transmission, alert dispatch, evacuation start, evacuation completion
7. Rigorous deterministic random seeding across all simulation entities
"""
import math
import random
import time
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

from app.services.path_planner import astar_planner

GRID_SIZE = 50
COMM_RANGE = 12.0
SAFE_SHELTER_X = 46.0
SAFE_SHELTER_Y = 25.0

class CivilianAgent:
    def __init__(self, cid: int, start_x: float, start_y: float, speed: float):
        self.id = f"CIV-{cid:03d}"
        self.x = start_x
        self.y = start_y
        self.evac_started = False
        self.evac_start_time: Optional[float] = None
        self.evac_completed = False
        self.completion_time: Optional[float] = None
        self.is_trapped = False
        self.path: List[Tuple[int, int]] = []
        self.current_waypoint_idx = 0
        self.speed = speed  # Grid units per simulation step (injected from deterministic trial RNG)

    @property
    def evacuation_duration_sec(self) -> Optional[float]:
        """Calculates transit duration from evacuation start to completion."""
        if self.evac_completed and self.completion_time is not None and self.evac_start_time is not None:
            return round(self.completion_time - self.evac_start_time, 2)
        return None

    @property
    def total_response_time_sec(self) -> Optional[float]:
        """Calculates total emergency response time from scenario trigger (t=0) to completion."""
        if self.evac_completed and self.completion_time is not None:
            return round(self.completion_time, 2)
        return None

class SimAgent:
    def __init__(self, aid: str, atype: str, start_x: float, start_y: float):
        self.id = aid
        self.type = atype  # UAV, USV, GROUND
        self.x = start_x
        self.y = start_y
        self.vx = 0.0
        self.vy = 0.0
        self.target_x = start_x
        self.target_y = start_y
        self.pbest_x = start_x
        self.pbest_y = start_y
        self.status = "ACTIVE"
        self.battery = 100.0
        self.connected_neighbors: List[str] = []
        self.messages_sent = 0
        self.cells_explored = set()

class CoastalSimulationTrial:
    """
    Executes a single end-to-end simulation trial under exact scenario configuration.
    Fully deterministic when initialized with the same seed.
    """
    def __init__(
        self,
        trial_id: int,
        magnitude: float = 7.8,
        distance_km: float = 45.0,
        num_civilians: int = 40,
        sim_duration_steps: int = 150,
        enable_pso: bool = True,
        enable_astar: bool = True,
        enable_mesh: bool = True,
        is_centralized_baseline: bool = False,
        agent_failure_step: Optional[int] = 40,
        failed_agent_id: str = "UAV-101",
        seed: int = 42
    ):
        self.trial_id = trial_id
        self.magnitude = magnitude
        self.distance_km = distance_km
        self.num_civilians = num_civilians
        self.sim_duration = sim_duration_steps
        self.enable_pso = enable_pso
        self.enable_astar = enable_astar
        self.enable_mesh = enable_mesh
        self.is_centralized = is_centralized_baseline
        self.agent_failure_step = agent_failure_step
        self.failed_agent_id = failed_agent_id
        self.seed = seed

        # Deterministic random generator instances for this trial
        self.rng = random.Random(seed)
        self.np_rng = np.random.RandomState(seed)

        # Generate 50x50 bathymetry grid
        self.bathymetry = self._create_bathymetry()
        self.inundation_grid = self._init_inundation_grid()

        # Agents and population (all speeds and positions generated via self.rng)
        self.agents: Dict[str, SimAgent] = self._create_swarm()
        self.civilians: List[CivilianAgent] = self._create_civilians()

        # Explicit detection & alerting pipeline timestamps
        self.observation_time_sec: Optional[float] = None
        self.decision_time_sec: Optional[float] = None
        self.transmission_time_sec: Optional[float] = None
        self.alert_dispatched: bool = False
        self.alert_dispatch_time_sec: Optional[float] = None

        # Tracking metrics
        self.path_planning_attempts = 0
        self.path_planning_successes = 0
        self.total_messages = 0
        self.inundation_peak_m = 0.0

    def _create_bathymetry(self) -> List[List[float]]:
        grid = []
        for y in range(GRID_SIZE):
            row = []
            for x in range(GRID_SIZE):
                coast_x = 20.0 + 3.0 * math.sin(y / 5.0)
                dist_from_coast = x - coast_x
                if dist_from_coast < 0:
                    depth = dist_from_coast * 3.5 - 5.0 * math.cos(y / 8.0)
                    row.append(round(max(-200.0, depth), 2))
                else:
                    elevation = dist_from_coast * 2.2 + 2.0 * math.sin(x / 4.0) * math.cos(y / 4.0)
                    row.append(round(min(120.0, elevation), 2))
            grid.append(row)
        return grid

    def _init_inundation_grid(self) -> List[List[Dict[str, Any]]]:
        return [
            [
                {
                    "x": x,
                    "y": y,
                    "elevation_m": self.bathymetry[y][x],
                    "inundation_depth_m": 0.0,
                    "risk_score": 0.0
                }
                for x in range(GRID_SIZE)
            ]
            for y in range(GRID_SIZE)
        ]

    def _create_swarm(self) -> Dict[str, SimAgent]:
        agents = {}
        # 3 UAVs (Air)
        agents["UAV-101"] = SimAgent("UAV-101", "UAV", 12.0, 10.0)
        agents["UAV-102"] = SimAgent("UAV-102", "UAV", 22.0, 25.0)
        agents["UAV-103"] = SimAgent("UAV-103", "UAV", 35.0, 38.0)
        # 3 USVs (Sea)
        agents["USV-201"] = SimAgent("USV-201", "USV", 5.0, 12.0)
        agents["USV-202"] = SimAgent("USV-202", "USV", 8.0, 26.0)
        agents["USV-203"] = SimAgent("USV-203", "USV", 11.0, 40.0)
        # 3 Ground rovers (Land)
        agents["GRD-301"] = SimAgent("GRD-301", "GROUND", 26.0, 15.0)
        agents["GRD-302"] = SimAgent("GRD-302", "GROUND", 30.0, 28.0)
        agents["GRD-303"] = SimAgent("GRD-303", "GROUND", 38.0, 42.0)
        return agents

    def _create_civilians(self) -> List[CivilianAgent]:
        civs = []
        for i in range(self.num_civilians):
            # Civilians reside in coastal lowland zone strictly on dry land (x: 24.0 to 29.5, y: 8.0 to 42.0)
            cx = self.rng.uniform(24.0, 29.5)
            cy = self.rng.uniform(8.0, 42.0)
            # Injected deterministic speed per civilian agent
            speed = self.rng.uniform(0.38, 0.55)
            civs.append(CivilianAgent(i + 1, cx, cy, speed))
        return civs

    def _get_surge_height_at(self, x: float, y: float, t_sec: float) -> float:
        """
        Calculates instantaneous physical wave surge elevation at grid coordinates (x, y).
        Deep-ocean wave phase velocity v = sqrt(g * h) ~ 198 m/s (~713 km/h).
        Epicenter distance in km -> deep water travel time to coastal shoreline (x=20): ~85s.
        """
        if x < 20.0:
            # Offshore approach: wave propagates eastward across shelf toward shoreline at x=20
            time_to_x = 28.0 + (x * 2.85)  # reaches x=5 at ~42s, x=20 at 85s
        else:
            # Overland runup: wave crosses coastline at x=20 at t=85s and inundates coastal plain
            time_to_x = 85.0 + (x - 20.0) * 1.5

        # Abe's empirical source displacement scaling: H0 = 10^(0.52*M - 3.4)
        log_h0 = 0.52 * self.magnitude - 3.4
        wave_peak = (10 ** log_h0) * 1.15  # ~5.2 meters for M7.8

        if t_sec < time_to_x:
            return 0.0

        dt = t_sec - time_to_x
        # Solitary wave profile: H * sech^2(dt / width)
        return wave_peak / (math.cosh(dt / 35.0) ** 2)

    def _update_inundation(self, t_sec: float):
        """Propagates tsunami wave surge over the 50x50 coastal terrain."""
        max_surge = 0.0
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                elev = self.bathymetry[y][x]
                coast_x = 20.0 + 3.0 * math.sin(y / 5.0)
                dist_to_shore = max(0.0, x - coast_x)

                surge_at_cell = self._get_surge_height_at(x, y, t_sec)
                max_surge = max(max_surge, surge_at_cell)

                if elev <= 0:
                    depth = 0.0
                    risk = 0.0
                else:
                    # Inundation decays with terrain elevation and distance inland
                    depth = max(0.0, round(surge_at_cell - (0.35 * elev) - (0.05 * dist_to_shore), 2))
                    if depth <= 0.01:
                        risk = 0.0
                    elif depth < 0.5:
                        risk = 0.25
                    elif depth < 2.0:
                        risk = 0.65
                    else:
                        risk = 1.0

                self.inundation_grid[y][x]["inundation_depth_m"] = depth
                self.inundation_grid[y][x]["risk_score"] = risk

        self.inundation_peak_m = max(self.inundation_peak_m, max_surge)

    def run(self) -> Dict[str, Any]:
        """Executes full simulation trial loop."""
        start_clock = time.time()

        for step in range(self.sim_duration):
            t_sec = step * 2.0  # 2.0 seconds per discrete simulation step

            # 1. Update Inundation Wave Propagation
            self._update_inundation(t_sec)

            # 2. Inject Agent Failure if configured
            if self.agent_failure_step and step == self.agent_failure_step:
                if self.failed_agent_id in self.agents:
                    self.agents[self.failed_agent_id].status = "LOST"

            # 3. Detection and Alerting Pipeline Check
            if not self.alert_dispatched:
                if self.is_centralized:
                    # Centralized Baseline:
                    # Observation occurs when incoming surge reaches fixed coastal shoreline sensor (x = 20.0)
                    shore_surge = self._get_surge_height_at(20.0, 25.0, t_sec)
                    if shore_surge >= 0.30 and self.observation_time_sec is None:
                        self.observation_time_sec = t_sec
                        # Anomaly verification window (2 consecutive sensor samples = 4.0s)
                        self.decision_time_sec = self.observation_time_sec + 4.0
                        # Telemetry uplink to regional disaster HQ
                        self.transmission_time_sec = self.decision_time_sec + 6.0
                        # Modeled civil defense authority checklist, manual verification & siren activation delay:
                        protocol_delay = 95.0 + self.rng.uniform(-4.0, 4.0)
                        self.alert_dispatch_time_sec = self.transmission_time_sec + protocol_delay

                    if self.alert_dispatch_time_sec is not None and t_sec >= self.alert_dispatch_time_sec:
                        self.alert_dispatched = True

                else:
                    # Proposed Multi-Agent Swarm:
                    # Forward offshore USVs (x in [5, 11]) or coastal UAVs detect wave anomaly early
                    for a in self.agents.values():
                        if a.status == "ACTIVE" and a.type in ["USV", "UAV"] and a.x <= 20.0:
                            surge_at_agent = self._get_surge_height_at(a.x, a.y, t_sec)
                            if surge_at_agent >= 0.30 and self.observation_time_sec is None:
                                self.observation_time_sec = t_sec
                                # Anomaly verification window (4.0s)
                                self.decision_time_sec = self.observation_time_sec + 4.0
                                # Local mesh broadcast across neighbor relays (~1.5s multi-hop delay)
                                mesh_delay = 1.5 + self.rng.uniform(-0.5, 0.5)
                                self.transmission_time_sec = self.decision_time_sec + mesh_delay
                                # Autonomous edge siren broadcast occurs immediately upon mesh consensus
                                self.alert_dispatch_time_sec = self.transmission_time_sec
                                break

                    if self.alert_dispatch_time_sec is not None and t_sec >= self.alert_dispatch_time_sec:
                        self.alert_dispatched = True


            # 4. Swarm Proximity Mesh & Communication
            active_agents = [a for a in self.agents.values() if a.status == "ACTIVE"]
            for a in self.agents.values():
                a.connected_neighbors.clear()

            if self.enable_mesh and not self.is_centralized:
                for i in range(len(active_agents)):
                    for j in range(i + 1, len(active_agents)):
                        a1, a2 = active_agents[i], active_agents[j]
                        dist = math.sqrt((a1.x - a2.x)**2 + (a1.y - a2.y)**2)
                        if dist <= COMM_RANGE:
                            a1.connected_neighbors.append(a2.id)
                            a2.connected_neighbors.append(a1.id)
                            self.total_messages += 2
            elif self.is_centralized:
                # In centralized architecture, each active agent sends telemetry to central gateway
                self.total_messages += len(active_agents)

            # 5. Agent Movement & Search Coordination
            for a in active_agents:
                # Mark explored cell
                ix = int(min(GRID_SIZE - 1, max(0, a.x)))
                iy = int(min(GRID_SIZE - 1, max(0, a.y)))
                radius = 3 if a.type == "UAV" else 2
                for fx in range(max(0, ix - radius), min(GRID_SIZE, ix + radius + 1)):
                    for fy in range(max(0, iy - radius), min(GRID_SIZE, iy + radius + 1)):
                        a.cells_explored.add((fx, fy))

                # Coordination strategy
                if self.enable_pso:
                    # PSO updates
                    w, c1, c2 = 0.5, 1.2, 1.5
                    gbest_x, gbest_y = a.target_x, a.target_y

                    if self.enable_mesh and a.connected_neighbors:
                        nbrs = [self.agents[nid] for nid in a.connected_neighbors if self.agents[nid].status == "ACTIVE"]
                        if nbrs:
                            best_nbr = max(nbrs, key=lambda n: len(n.cells_explored))
                            gbest_x, gbest_y = best_nbr.target_x, best_nbr.target_y

                    r1, r2 = self.rng.random(), self.rng.random()
                    max_speed = 1.8 if a.type == "UAV" else (1.0 if a.type == "USV" else 0.7)

                    a.vx = w * a.vx + c1 * r1 * (a.target_x - a.x) + c2 * r2 * (gbest_x - a.x)
                    a.vy = w * a.vy + c1 * r1 * (a.target_y - a.y) + c2 * r2 * (gbest_y - a.y)

                    spd = math.sqrt(a.vx**2 + a.vy**2)
                    if spd > max_speed:
                        a.vx = (a.vx / spd) * max_speed
                        a.vy = (a.vy / spd) * max_speed

                    # Validate candidate movement with A* terrain feasibility
                    cand_x = max(0.0, min(float(GRID_SIZE - 1), a.x + a.vx))
                    cand_y = max(0.0, min(float(GRID_SIZE - 1), a.y + a.vy))
                    cost = astar_planner.get_cell_cost(
                        int(round(cand_x)), int(round(cand_y)), a.type,
                        self.bathymetry, self.inundation_grid
                    )
                    if not math.isinf(cost):
                        a.x = cand_x
                        a.y = cand_y
                    else:
                        a.vx = 0.0
                        a.vy = 0.0

                    if math.sqrt((a.x - a.target_x)**2 + (a.y - a.target_y)**2) < 2.0:
                        a.target_x = self.rng.uniform(4.0, GRID_SIZE - 5.0)
                        a.target_y = self.rng.uniform(4.0, GRID_SIZE - 5.0)
                else:
                    # Ablation: Without PSO -> Fixed periodic patrol lines
                    # Agents move along fixed patrol paths
                    patrol_speed = 0.6
                    a.x = max(0.0, min(float(GRID_SIZE - 1), a.x + math.cos(step * 0.1) * patrol_speed))
                    a.y = max(0.0, min(float(GRID_SIZE - 1), a.y + math.sin(step * 0.1) * patrol_speed))

            # 6. Civilian Hazard Exposure & Evacuation Dynamics
            for civ in self.civilians:
                if civ.evac_completed or civ.is_trapped:
                    continue

                cx_int = int(min(GRID_SIZE - 1, max(0, civ.x)))
                cy_int = int(min(GRID_SIZE - 1, max(0, civ.y)))
                current_inundation = self.inundation_grid[cy_int][cx_int]["inundation_depth_m"]

                # Check if civilian is overtaken/trapped by lethal floodwater (>= 1.2m)
                if current_inundation >= 1.2:
                    civ.is_trapped = True
                    continue

                # Evacuation begins once alert is dispatched
                if self.alert_dispatched:
                    if not civ.evac_started:
                        civ.evac_started = True
                        civ.evac_start_time = t_sec

                        # Compute evacuation route to safe shelter
                        self.path_planning_attempts += 1
                        if self.enable_astar:
                            plan = astar_planner.find_path(
                                (civ.x, civ.y),
                                (SAFE_SHELTER_X, SAFE_SHELTER_Y),
                                agent_type="CIVILIAN",
                                bathymetry_grid=self.bathymetry,
                                inundation_grid=self.inundation_grid
                            )
                            if plan["success"]:
                                civ.path = plan["path"]
                                self.path_planning_successes += 1
                            else:
                                civ.path = [(int(SAFE_SHELTER_X), int(SAFE_SHELTER_Y))]
                        else:
                            # Ablation: Without A* -> Uninformed direct line to shelter
                            civ.path = [(int(SAFE_SHELTER_X), int(SAFE_SHELTER_Y))]
                            if self.inundation_grid[int(civ.y)][int(civ.x)]["inundation_depth_m"] < 0.2:
                                self.path_planning_successes += 1

                    # Move toward next waypoint
                    if civ.path and civ.current_waypoint_idx < len(civ.path):
                        target_wp = civ.path[civ.current_waypoint_idx]
                        dx = target_wp[0] - civ.x
                        dy = target_wp[1] - civ.y
                        dist_to_wp = math.sqrt(dx**2 + dy**2)
                        if dist_to_wp < 1.0:
                            civ.current_waypoint_idx += 1
                        else:
                            civ.x += (dx / dist_to_wp) * civ.speed
                            civ.y += (dy / dist_to_wp) * civ.speed

                    # Check arrival at safe shelter
                    if math.sqrt((civ.x - SAFE_SHELTER_X)**2 + (civ.y - SAFE_SHELTER_Y)**2) < 2.5:
                        civ.evac_completed = True
                        civ.completion_time = t_sec

        # ----------------- TRIAL METRICS CALCULATION -----------------
        # 1. Search coverage
        total_cells_covered = set()
        for a in self.agents.values():
            total_cells_covered.update(a.cells_explored)
        search_coverage_pct = round((len(total_cells_covered) / (GRID_SIZE * GRID_SIZE)) * 100.0, 2)

        # 2. Path planning success rate
        if self.path_planning_attempts > 0:
            path_success_rate = round((self.path_planning_successes / self.path_planning_attempts) * 100.0, 2)
        else:
            path_success_rate = 0.0

        # 3. Civilian evacuation metrics
        evacuated_civilians = [c for c in self.civilians if c.evac_completed]
        trapped_civilians = [c for c in self.civilians if c.is_trapped]
        in_transit_civilians = [c for c in self.civilians if not c.evac_completed and not c.is_trapped]
        evac_completion_pct = round((len(evacuated_civilians) / self.num_civilians) * 100.0, 2)

        # Average transit duration strictly across successfully evacuated civilians:
        # duration = completion_time - evac_start_time
        if evacuated_civilians:
            durations = [c.evacuation_duration_sec for c in evacuated_civilians if c.evacuation_duration_sec is not None]
            avg_evac_duration_sec = round(float(np.mean(durations)), 2) if durations else 0.0
            avg_evac_duration_min = round(avg_evac_duration_sec / 60.0, 2)

            total_response_times = [c.total_response_time_sec for c in evacuated_civilians if c.total_response_time_sec is not None]
            avg_total_response_sec = round(float(np.mean(total_response_times)), 2) if total_response_times else 0.0
            avg_total_response_min = round(avg_total_response_sec / 60.0, 2)
        else:
            avg_evac_duration_sec = 0.0
            avg_evac_duration_min = 0.0
            avg_total_response_sec = round(self.sim_duration * 2.0, 2)
            avg_total_response_min = round(avg_total_response_sec / 60.0, 2)

        det_to_alert_time = round(self.alert_dispatch_time_sec or (self.sim_duration * 2.0), 2)
        exec_duration_ms = round((time.time() - start_clock) * 1000.0, 2)

        return {
            "trial_id": self.trial_id,
            "seed": self.seed,
            "architecture": "Centralized Baseline" if self.is_centralized else "Proposed Multi-Agent Swarm",
            # Detection & alert pipeline timestamps (in seconds)
            "anomaly_observation_time_sec": round(self.observation_time_sec, 2) if self.observation_time_sec is not None else None,
            "observation_time_sec": round(self.observation_time_sec, 2) if self.observation_time_sec is not None else None,
            "decision_time_sec": round(self.decision_time_sec, 2) if self.decision_time_sec is not None else None,
            "transmission_time_sec": round(self.transmission_time_sec, 2) if self.transmission_time_sec is not None else None,
            "alert_dispatch_time_sec": round(self.alert_dispatch_time_sec, 2) if self.alert_dispatch_time_sec is not None else None,
            "detection_to_alert_time_sec": det_to_alert_time,
            # Evacuation metrics
            "evacuation_duration_sec": avg_evac_duration_sec,
            "evacuation_duration_min": avg_evac_duration_min,
            "evacuation_time_min": avg_evac_duration_min,  # Compatibility alias
            "total_response_time_sec": avg_total_response_sec,
            "total_response_time_min": avg_total_response_min,
            "evacuation_completion_pct": evac_completion_pct,
            "evacuation_success_rate_pct": evac_completion_pct,  # Compatibility alias
            "civilians_evacuated": len(evacuated_civilians),
            "civilians_trapped": len(trapped_civilians),
            "civilians_in_transit": len(in_transit_civilians),
            "total_civilians": self.num_civilians,
            # Swarm coverage & path planning
            "search_coverage_pct": search_coverage_pct,
            "path_planning_success_pct": path_success_rate,
            "communication_messages": self.total_messages,
            "execution_duration_ms": exec_duration_ms
        }

class BenchmarkRunner:
    """Runs parameterized multi-trial simulations comparing Centralized Baseline vs Proposed Swarm."""
    def __init__(self, num_trials: int = 30, base_seed: int = 100):
        self.num_trials = num_trials
        self.base_seed = base_seed

    def run_benchmark(
        self,
        magnitude: float = 7.8,
        distance_km: float = 45.0
    ) -> Dict[str, Any]:
        baseline_trials = []
        swarm_trials = []

        for i in range(self.num_trials):
            seed = self.base_seed + i
            # 1. Run Centralized Baseline
            trial_base = CoastalSimulationTrial(
                trial_id=i + 1,
                magnitude=magnitude,
                distance_km=distance_km,
                is_centralized_baseline=True,
                enable_pso=False,
                enable_astar=True,
                enable_mesh=False,
                seed=seed
            )
            res_base = trial_base.run()
            baseline_trials.append(res_base)

            # 2. Run Proposed Multi-Agent Swarm (CoastGuard Twin)
            trial_swarm = CoastalSimulationTrial(
                trial_id=i + 1,
                magnitude=magnitude,
                distance_km=distance_km,
                is_centralized_baseline=False,
                enable_pso=True,
                enable_astar=True,
                enable_mesh=True,
                seed=seed
            )
            res_swarm = trial_swarm.run()
            swarm_trials.append(res_swarm)

        # Compute aggregate statistics
        metric_keys = [
            ("detection_to_alert_time_sec", "Detection-to-Alert Time", "seconds", True),
            ("evacuation_duration_min", "Evacuation Transit Duration", "minutes", True),
            ("total_response_time_min", "Total Emergency Response Time", "minutes", True),
            ("search_coverage_pct", "Search-Area Coverage", "%", False),
            ("path_planning_success_pct", "Path-Planning Success Rate", "%", False),
            ("evacuation_completion_pct", "Evacuation Completion Rate", "%", False)
        ]

        comparison_metrics = []
        for key, title, unit, lower_is_better in metric_keys:
            base_vals = [t[key] for t in baseline_trials]
            swarm_vals = [t[key] for t in swarm_trials]

            b_mean = float(np.mean(base_vals))
            b_std = float(np.std(base_vals, ddof=1)) if len(base_vals) > 1 else 0.0
            s_mean = float(np.mean(swarm_vals))
            s_std = float(np.std(swarm_vals, ddof=1)) if len(swarm_vals) > 1 else 0.0

            # 95% Confidence Interval: margin = 1.96 * (std / sqrt(N))
            n = len(base_vals)
            b_ci95 = 1.96 * (b_std / math.sqrt(n)) if n > 0 else 0.0
            s_ci95 = 1.96 * (s_std / math.sqrt(n)) if n > 0 else 0.0

            # Improvement calculation
            if lower_is_better:
                improvement = ((b_mean - s_mean) / b_mean) * 100.0 if b_mean > 0 else 0.0
            else:
                improvement = ((s_mean - b_mean) / b_mean) * 100.0 if b_mean > 0 else 0.0

            comparison_metrics.append({
                "key": key,
                "title": title,
                "unit": unit,
                "lower_is_better": lower_is_better,
                "baseline_mean": round(b_mean, 2),
                "baseline_std": round(b_std, 2),
                "baseline_ci95": [round(b_mean - b_ci95, 2), round(b_mean + b_ci95, 2)],
                "proposed_mean": round(s_mean, 2),
                "proposed_std": round(s_std, 2),
                "proposed_ci95": [round(s_mean - s_ci95, 2), round(s_mean + s_ci95, 2)],
                "improvement_percentage": round(improvement, 1)
            })

        return {
            "metadata": {
                "num_trials": self.num_trials,
                "magnitude": magnitude,
                "distance_km": distance_km,
                "base_seed": self.base_seed,
                "timestamp": round(time.time(), 2)
            },
            "comparison_metrics": comparison_metrics,
            "raw_trials": {
                "baseline": baseline_trials,
                "proposed_swarm": swarm_trials
            }
        }

    def run_ablation_study(
        self,
        magnitude: float = 7.8,
        distance_km: float = 45.0,
        trials_per_variant: int = 15
    ) -> Dict[str, Any]:
        """
        Executes ablation study across 5 architectural configurations:
        1. Full Proposed System (Swarm + PSO + A* + Mesh)
        2. Swarm without PSO (Fixed Patrol)
        3. Swarm without A* (Direct-line Navigation)
        4. Swarm without Mesh Communication (Isolated Agents)
        5. Centralized Baseline (Single Hub Controller)
        """
        variants = [
            ("Full Proposed System (PSO + A* + Mesh)", False, True, True, True),
            ("Swarm w/o PSO (Fixed Patrol)", False, False, True, True),
            ("Swarm w/o A* (Direct Path)", False, True, False, True),
            ("Swarm w/o Mesh (Isolated Agents)", False, True, True, False),
            ("Centralized Baseline System", True, False, True, False)
        ]

        ablation_summary = []
        raw_variant_trials = {}

        for var_name, is_central, pso, astar, mesh in variants:
            trials = []
            for i in range(trials_per_variant):
                seed = self.base_seed + i
                trial = CoastalSimulationTrial(
                    trial_id=i + 1,
                    magnitude=magnitude,
                    distance_km=distance_km,
                    is_centralized_baseline=is_central,
                    enable_pso=pso,
                    enable_astar=astar,
                    enable_mesh=mesh,
                    seed=seed
                )
                trials.append(trial.run())

            raw_variant_trials[var_name] = trials

            det_vals = [t["detection_to_alert_time_sec"] for t in trials]
            evac_vals = [t["evacuation_duration_min"] for t in trials]
            cov_vals = [t["search_coverage_pct"] for t in trials]
            path_vals = [t["path_planning_success_pct"] for t in trials]
            success_vals = [t["evacuation_completion_pct"] for t in trials]

            ablation_summary.append({
                "variant_name": var_name,
                "pso_enabled": pso,
                "astar_enabled": astar,
                "mesh_enabled": mesh,
                "is_centralized": is_central,
                "metrics": {
                    "detection_time_mean": round(float(np.mean(det_vals)), 2),
                    "detection_time_std": round(float(np.std(det_vals)), 2),
                    "evacuation_duration_mean": round(float(np.mean(evac_vals)), 2),
                    "evacuation_duration_std": round(float(np.std(evac_vals)), 2),
                    "evacuation_time_mean": round(float(np.mean(evac_vals)), 2),
                    "evacuation_time_std": round(float(np.std(evac_vals)), 2),
                    "coverage_mean": round(float(np.mean(cov_vals)), 2),
                    "coverage_std": round(float(np.std(cov_vals)), 2),
                    "path_success_mean": round(float(np.mean(path_vals)), 2),
                    "path_success_std": round(float(np.std(path_vals)), 2),
                    "evacuation_completion_mean": round(float(np.mean(success_vals)), 2),
                    "evacuation_completion_std": round(float(np.std(success_vals)), 2),
                    "evacuation_success_mean": round(float(np.mean(success_vals)), 2),
                    "evacuation_success_std": round(float(np.std(success_vals)), 2)
                }
            })

        return {
            "metadata": {
                "magnitude": magnitude,
                "distance_km": distance_km,
                "trials_per_variant": trials_per_variant,
                "base_seed": self.base_seed
            },
            "ablation_summary": ablation_summary,
            "raw_trials": raw_variant_trials
        }

benchmark_runner = BenchmarkRunner()
