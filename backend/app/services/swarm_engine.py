"""
Layer 3 — Swarm Intelligence Coordination Engine
Simulates heterogeneous multi-agent swarm (UAVs, USVs, Ground Robots)
with decentralized PSO task allocation, proximity mesh topology,
A* path planning, deterministic sector assignment, and hazard-safe waypoint tracking.
"""
import math
import random
import time
from typing import Dict, List, Any, Optional
from app.services.data_sim_engine import GRID_SIZE

COMM_RANGE = 12.0  # Maximum mesh communication range in grid units

class SwarmAgent:
    def __init__(self, agent_id: str, agent_type: str, start_x: float, start_y: float):
        self.id = agent_id
        self.type = agent_type  # UAV, USV, GROUND
        self.x = start_x
        self.y = start_y
        self.vx = 0.0
        self.vy = 0.0
        self.status = "ACTIVE"  # ACTIVE, RETURNING, LOST
        self.battery = 95.0
        self.confidence_report = 0.92
        
        # Target assignment and path
        self.target_x = start_x
        self.target_y = start_y
        self.pbest_x = start_x
        self.pbest_y = start_y
        self.pbest_val = 0.0
        self.current_path: List[List[int]] = []

        # Deterministic sector assignment (avoids process-randomized hash())
        sector_idx = (sum(ord(c) for c in agent_id) % 4) + 1
        self.assigned_sector = f"Sector-{sector_idx}"
        self.connected_neighbors: List[str] = []

    def update_battery(self):
        if self.status == "ACTIVE":
            discharge = 0.12 if self.type == "UAV" else (0.08 if self.type == "GROUND" else 0.05)
            self.battery = max(0.0, self.battery - discharge)
            if self.battery < 15.0:
                self.status = "RETURNING"
            elif self.battery <= 0.0:
                self.status = "LOST"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "position": {"x": round(self.x, 2), "y": round(self.y, 2)},
            "target": {"x": round(self.target_x, 2), "y": round(self.target_y, 2)},
            "status": self.status,
            "battery": round(self.battery, 1),
            "confidence_report": self.confidence_report,
            "assigned_sector": self.assigned_sector,
            "connected_neighbors": list(self.connected_neighbors),
            "current_path": self.current_path
        }

class SwarmEngine:
    def __init__(self):
        self.agents: Dict[str, SwarmAgent] = {}
        self.is_satellite_failover_active = False
        self._initialize_default_swarm()

    def toggle_satellite_failover(self, active: Optional[bool] = None) -> bool:
        if active is not None:
            self.is_satellite_failover_active = active
        else:
            self.is_satellite_failover_active = not self.is_satellite_failover_active
        return self.is_satellite_failover_active

    def _initialize_default_swarm(self):
        # 3 UAVs (Air)
        self.agents["UAV-101"] = SwarmAgent("UAV-101", "UAV", 10.0, 10.0)
        self.agents["UAV-102"] = SwarmAgent("UAV-102", "UAV", 25.0, 25.0)
        self.agents["UAV-103"] = SwarmAgent("UAV-103", "UAV", 40.0, 35.0)

        # 3 USVs (Sea)
        self.agents["USV-201"] = SwarmAgent("USV-201", "USV", 5.0, 15.0)
        self.agents["USV-202"] = SwarmAgent("USV-202", "USV", 8.0, 30.0)
        self.agents["USV-203"] = SwarmAgent("USV-203", "USV", 12.0, 42.0)

        # 3 Ground Robots (Land)
        self.agents["GRD-301"] = SwarmAgent("GRD-301", "GROUND", 28.0, 12.0)
        self.agents["GRD-302"] = SwarmAgent("GRD-302", "GROUND", 35.0, 28.0)
        self.agents["GRD-303"] = SwarmAgent("GRD-303", "GROUND", 45.0, 40.0)

    def deploy_agent(self, agent_type: str, x: float, y: float) -> SwarmAgent:
        idx = len(self.agents) + 1
        prefix = "UAV" if agent_type == "UAV" else ("USV" if agent_type == "USV" else "GRD")
        agent_id = f"{prefix}-{idx:03d}"
        agent = SwarmAgent(agent_id, agent_type, x, y)
        self.agents[agent_id] = agent
        return agent

    def simulate_agent_loss(self, agent_id: str):
        if agent_id in self.agents:
            self.agents[agent_id].status = "LOST"
            self.agents[agent_id].battery = 0.0

    def reassign_coverage(self, sector_name: str, target_x: float, target_y: float):
        for agent in self.agents.values():
            if agent.status == "ACTIVE" and agent.assigned_sector == sector_name:
                agent.target_x = target_x
                agent.target_y = target_y

    def update_mesh_topology(self) -> Dict[str, Any]:
        """Calculates mesh network edges based on physical proximity threshold."""
        active_agents = [a for a in self.agents.values() if a.status != "LOST"]
        
        # Reset connections
        for a in self.agents.values():
            a.connected_neighbors.clear()

        edges = []
        for i in range(len(active_agents)):
            for j in range(i + 1, len(active_agents)):
                a1 = active_agents[i]
                a2 = active_agents[j]

                dist = math.sqrt((a1.x - a2.x)**2 + (a1.y - a2.y)**2)
                if dist <= COMM_RANGE:
                    a1.connected_neighbors.append(a2.id)
                    a2.connected_neighbors.append(a1.id)
                    edges.append({
                        "source": a1.id,
                        "target": a2.id,
                        "distance": round(dist, 2),
                        "signal_strength": round(max(0.1, 1.0 - (dist / COMM_RANGE)), 2)
                    })

        nodes = [a.to_dict() for a in self.agents.values()]
        return {
            "nodes": nodes,
            "edges": edges,
            "comm_range": COMM_RANGE,
            "is_satellite_failover_active": self.is_satellite_failover_active,
            "channel_type": "LEO_SATELLITE" if self.is_satellite_failover_active else "TERRESTRIAL_MESH",
            "total_active": len([a for a in self.agents.values() if a.status == "ACTIVE"]),
            "total_lost": len([a for a in self.agents.values() if a.status == "LOST"]),
        }

    def tick_pso_and_pathfinding(self, risk_grid: Optional[List[List[Dict[str, Any]]]] = None):
        """
        Executes decentralized PSO movement + mesh coverage redistribution.
        Ensures agent movement respects A* obstacle boundaries and never steps into lethal hazards.
        """
        from app.services.path_planner import astar_planner
        from app.services.data_sim_engine import sim_engine

        # Update mesh connections
        topology = self.update_mesh_topology()
        lost_agent_ids = [a.id for a in self.agents.values() if a.status == "LOST"]

        for agent in self.agents.values():
            if agent.status != "ACTIVE":
                agent.update_battery()
                continue

            max_speed = 1.8 if agent.type == "UAV" else (1.0 if agent.type == "USV" else 0.7)

            # PSO parameters
            w = 0.5   # Inertia
            c1 = 1.2  # Cognitive factor
            c2 = 1.5  # Social neighborhood factor

            # Neighborhood best target among connected active neighbors
            gbest_x, gbest_y = agent.target_x, agent.target_y
            if agent.connected_neighbors:
                neighbor_agents = [
                    self.agents[nid] for nid in agent.connected_neighbors
                    if nid in self.agents and self.agents[nid].status == "ACTIVE"
                ]
                if neighbor_agents:
                    target_neighbor = max(neighbor_agents, key=lambda n: n.battery)
                    gbest_x, gbest_y = target_neighbor.target_x, target_neighbor.target_y

            # Replan A* path if needed
            bathymetry_matrix = sim_engine.bathymetry_grid.tolist()
            if risk_grid is not None and (not agent.current_path or len(agent.current_path) < 2):
                plan = astar_planner.find_path(
                    (agent.x, agent.y),
                    (agent.target_x, agent.target_y),
                    agent_type=agent.type,
                    bathymetry_grid=bathymetry_matrix,
                    inundation_grid=risk_grid
                )
                if plan["success"] and len(plan["path"]) > 1:
                    agent.current_path = [[int(p[0]), int(p[1])] for p in plan["path"][:8]]

            # Steer along A* path waypoint if available, else toward target
            steer_target_x, steer_target_y = agent.target_x, agent.target_y
            if agent.current_path and len(agent.current_path) > 1:
                next_wp = agent.current_path[1]
                steer_target_x, steer_target_y = float(next_wp[0]), float(next_wp[1])
                if math.sqrt((agent.x - steer_target_x)**2 + (agent.y - steer_target_y)**2) < 1.2:
                    agent.current_path.pop(0)

            r1, r2 = random.random(), random.random()
            agent.vx = w * agent.vx + c1 * r1 * (steer_target_x - agent.x) + c2 * r2 * (gbest_x - agent.x)
            agent.vy = w * agent.vy + c1 * r1 * (steer_target_y - agent.y) + c2 * r2 * (gbest_y - agent.y)

            # Clamp velocity
            speed = math.sqrt(agent.vx**2 + agent.vy**2)
            if speed > max_speed:
                agent.vx = (agent.vx / speed) * max_speed
                agent.vy = (agent.vy / speed) * max_speed

            # Validate candidate destination cell before moving (hazard barrier enforcement)
            cand_x = max(0.0, min(float(GRID_SIZE - 1), agent.x + agent.vx))
            cand_y = max(0.0, min(float(GRID_SIZE - 1), agent.y + agent.vy))

            cand_cost = astar_planner.get_cell_cost(
                int(round(cand_x)), int(round(cand_y)), agent.type,
                bathymetry_matrix, risk_grid
            )

            if not math.isinf(cand_cost):
                agent.x = cand_x
                agent.y = cand_y
            else:
                # If PSO forces pull into an obstacle/water barrier, follow valid A* waypoint directly
                if agent.current_path and len(agent.current_path) > 1:
                    wp = agent.current_path[1]
                    dx = wp[0] - agent.x
                    dy = wp[1] - agent.y
                    d = math.sqrt(dx**2 + dy**2)
                    if d > 0.01:
                        step_len = min(max_speed, d)
                        agent.x += (dx / d) * step_len
                        agent.y += (dy / d) * step_len
                else:
                    agent.vx = 0.0
                    agent.vy = 0.0

            # Target reached: pick new random exploration waypoint
            if math.sqrt((agent.x - agent.target_x)**2 + (agent.y - agent.target_y)**2) < 2.0:
                agent.target_x = random.uniform(5.0, GRID_SIZE - 5.0)
                agent.target_y = random.uniform(5.0, GRID_SIZE - 5.0)
                agent.current_path.clear()

            agent.update_battery()

        return topology

swarm_engine = SwarmEngine()
