"""
A* Path Planning Service for Coastal Hazard Navigation
Implements 2D grid graph search with:
- Elevation slope-aware traversal cost
- Inundation hazard avoidance and barrier thresholds
- Heterogeneous vehicle constraints (UAV air, USV sea, GROUND land, CIVILIAN)
- Start and goal traversability validation
- Strict diagonal corner-cutting prevention
- Octile heuristic distance function
- Fallback handling for unreachable destinations
"""
import math
import heapq
from typing import List, Tuple, Dict, Any, Optional

class AStarPlanner:
    def __init__(self, grid_size: int = 50):
        self.grid_size = grid_size

    def heuristic(self, a: Tuple[int, int], b: Tuple[int, int]) -> float:
        """Octile distance heuristic for 8-connected grid navigation."""
        dx = abs(a[0] - b[0])
        dy = abs(a[1] - b[1])
        # Diagonal cost sqrt(2) ~ 1.414, straight cost 1.0
        return 1.0 * (dx + dy) + (1.414 - 2.0) * min(dx, dy)

    def get_cell_cost(
        self,
        x: int,
        y: int,
        agent_type: str,
        bathymetry_grid: List[List[float]],
        inundation_grid: Optional[List[List[Dict[str, Any]]]] = None,
        from_x: Optional[int] = None,
        from_y: Optional[int] = None,
        hazard_weight: float = 10.0
    ) -> float:
        """
        Calculates cell traversal cost and traversability.
        Returns float cost, or infinity (math.inf) if impassable obstacle.
        """
        if not (0 <= x < self.grid_size and 0 <= y < self.grid_size):
            return math.inf

        elevation = bathymetry_grid[y][x]
        inundation_depth = 0.0
        risk_score = 0.0

        if inundation_grid is not None and y < len(inundation_grid) and x < len(inundation_grid[y]):
            cell_data = inundation_grid[y][x]
            inundation_depth = cell_data.get("inundation_depth_m", 0.0)
            risk_score = cell_data.get("risk_score", 0.0)

        # Agent-specific terrain feasibility constraints
        if agent_type == "USV":
            # Sea vehicle: requires water (elevation <= 0 or flooded land > 0.8m)
            if elevation > 0 and inundation_depth < 0.8:
                return math.inf  # Dry land is impassable for USV
            return 1.0

        elif agent_type in ("GROUND", "CIVILIAN"):
            # Land vehicle / civilian: cannot travel in deep ocean (elevation <= 0)
            if elevation <= 0:
                return math.inf
            # Deep inundation (>= 1.5m) is impassable / lethal barrier
            if inundation_depth >= 1.5:
                return math.inf

            # Slope difficulty penalty based on elevation difference from source cell
            if from_x is not None and from_y is not None:
                from_elevation = bathymetry_grid[from_y][from_x]
                delta_z = elevation - from_elevation
                slope_penalty = max(0.0, delta_z * 0.05)
            else:
                slope_penalty = 0.0

            # Hazard penalty based on water depth and risk score
            hazard_penalty = (inundation_depth * hazard_weight) + (risk_score * 5.0)
            return 1.0 + hazard_penalty + slope_penalty

        elif agent_type == "UAV":
            # Air vehicle: can traverse over both land and sea; minor turbulence penalty near high surge risk
            return 1.0 + (risk_score * 0.5)

        return 1.0

    def find_path(
        self,
        start: Tuple[int, int],
        goal: Tuple[int, int],
        agent_type: str,
        bathymetry_grid: List[List[float]],
        inundation_grid: Optional[List[List[Dict[str, Any]]]] = None,
        max_expansions: int = 5000
    ) -> Dict[str, Any]:
        """
        Executes A* search from start to goal coordinates.
        Returns:
            success: bool
            path: list of (x, y) coordinates
            path_cost: total travel cost
            nodes_expanded: search efficiency count
            message: status string
        """
        start_x, start_y = int(round(start[0])), int(round(start[1]))
        goal_x, goal_y = int(round(goal[0])), int(round(goal[1]))

        # Boundary checks
        if not (0 <= start_x < self.grid_size and 0 <= start_y < self.grid_size):
            return {
                "success": False,
                "path": [],
                "path_cost": math.inf,
                "nodes_expanded": 0,
                "message": f"Start position ({start_x}, {start_y}) is out of grid boundaries."
            }

        if not (0 <= goal_x < self.grid_size and 0 <= goal_y < self.grid_size):
            return {
                "success": False,
                "path": [],
                "path_cost": math.inf,
                "nodes_expanded": 0,
                "message": f"Goal position ({goal_x}, {goal_y}) is out of grid boundaries."
            }

        start_node = (start_x, start_y)
        goal_node = (goal_x, goal_y)

        # 1. Validate start cell traversability
        start_cost = self.get_cell_cost(
            start_x, start_y, agent_type, bathymetry_grid, inundation_grid
        )
        if math.isinf(start_cost):
            return {
                "success": False,
                "path": [],
                "path_cost": math.inf,
                "nodes_expanded": 0,
                "message": f"Start position {start_node} is impassable for agent type '{agent_type}'."
            }

        # 2. Validate goal cell traversability
        goal_cost = self.get_cell_cost(
            goal_x, goal_y, agent_type, bathymetry_grid, inundation_grid
        )
        if math.isinf(goal_cost):
            return {
                "success": False,
                "path": [],
                "path_cost": math.inf,
                "nodes_expanded": 0,
                "message": f"Goal position {goal_node} is impassable for agent type '{agent_type}'."
            }

        if start_node == goal_node:
            return {
                "success": True,
                "path": [start_node],
                "path_cost": 0.0,
                "nodes_expanded": 1,
                "message": "Start equals goal."
            }

        # Priority queue stores tuples: (f_score, g_score, current_node)
        open_set = []
        heapq.heappush(open_set, (self.heuristic(start_node, goal_node), 0.0, start_node))

        came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}
        g_scores: Dict[Tuple[int, int], float] = {start_node: 0.0}
        closed_set = set()

        # 8-directional neighbor offsets (dx, dy, step_cost)
        neighbors_delta = [
            (1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
            (1, 1, 1.414), (-1, 1, 1.414), (1, -1, 1.414), (-1, -1, 1.414)
        ]

        expansions = 0

        while open_set and expansions < max_expansions:
            expansions += 1
            _, current_g, current = heapq.heappop(open_set)

            if current in closed_set:
                continue
            closed_set.add(current)

            if current == goal_node:
                # Reconstruct path
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                path.reverse()
                return {
                    "success": True,
                    "path": path,
                    "path_cost": round(current_g, 2),
                    "nodes_expanded": expansions,
                    "message": "Optimal path found."
                }

            cx, cy = current
            for dx, dy, step_dist in neighbors_delta:
                nx, ny = cx + dx, cy + dy

                if not (0 <= nx < self.grid_size and 0 <= ny < self.grid_size):
                    continue

                neighbor = (nx, ny)
                if neighbor in closed_set:
                    continue

                # Strict diagonal corner-cutting prevention:
                # Moving from (cx, cy) to (cx+dx, cy+dy) requires that neither orthogonal adjacent cell is blocked.
                if dx != 0 and dy != 0:
                    ortho1_cost = self.get_cell_cost(
                        cx + dx, cy, agent_type, bathymetry_grid, inundation_grid
                    )
                    ortho2_cost = self.get_cell_cost(
                        cx, cy + dy, agent_type, bathymetry_grid, inundation_grid
                    )
                    if math.isinf(ortho1_cost) or math.isinf(ortho2_cost):
                        continue

                cell_cost = self.get_cell_cost(
                    nx, ny, agent_type, bathymetry_grid, inundation_grid,
                    from_x=cx, from_y=cy
                )

                if math.isinf(cell_cost):
                    continue  # Impassable barrier

                tentative_g = current_g + (step_dist * cell_cost)

                if neighbor not in g_scores or tentative_g < g_scores[neighbor]:
                    came_from[neighbor] = current
                    g_scores[neighbor] = tentative_g
                    f_score = tentative_g + self.heuristic(neighbor, goal_node)
                    heapq.heappush(open_set, (f_score, tentative_g, neighbor))

        # If goal unreachable, attempt best-effort fallback to closest node reached
        if came_from:
            closest_node = min(closed_set, key=lambda n: self.heuristic(n, goal_node))
            path = [closest_node]
            curr = closest_node
            while curr in came_from:
                curr = came_from[curr]
                path.append(curr)
            path.reverse()
            return {
                "success": False,
                "path": path,
                "path_cost": round(g_scores.get(closest_node, math.inf), 2),
                "nodes_expanded": expansions,
                "message": "Goal unreachable; path truncated to nearest accessible waypoint."
            }

        return {
            "success": False,
            "path": [],
            "path_cost": math.inf,
            "nodes_expanded": expansions,
            "message": "Search exhausted without finding a feasible route."
        }

astar_planner = AStarPlanner()
