"""
Layer 2 — Digital Twin Synchronization Engine
Fuses sensor streams into a synchronized digital twin state object,
computes cell-by-cell inundation risk over the 50x50 bathymetry grid,
and manages digital twin audit snapshots.
"""
import time
import math
import numpy as np
from typing import Dict, List, Any
from app.services.data_sim_engine import sim_engine, GRID_SIZE

class DigitalTwinService:
    def __init__(self):
        self.snapshots_history: List[Dict[str, Any]] = []

    def compute_inundation_risk_grid(self, sensor_snapshot: Dict[str, Any]) -> List[List[Dict[str, Any]]]:
        """
        Computes 50x50 inundation risk grid based on bathymetry,
        current sea-level anomaly, and shoreline state.
        Heuristic: Risk = f(elevation, distance_to_shore, anomaly_magnitude, shoreline_state)
        """
        bathymetry = sim_engine.bathymetry_grid
        anomaly = sensor_snapshot["sensors"]["dart_buoy"]["sea_level_anomaly_m"]
        shore_state = sensor_snapshot["sensors"]["shoreline_camera"]["state"]

        # Shoreline multiplier
        state_multiplier = 1.5 if shore_state == "SURGING" else (1.2 if shore_state == "RECEDING" else 1.0)
        effective_wave_height = max(0.0, anomaly) * state_multiplier

        risk_grid: List[List[Dict[str, Any]]] = []

        for y in range(GRID_SIZE):
            row = []
            for x in range(GRID_SIZE):
                elevation = bathymetry[y, x]
                
                # Approximate distance from coastline (x=20 curve)
                coast_x = 20.0 + 3.0 * math.sin(y / 5.0)
                dist_to_shore = max(0.0, x - coast_x)

                if elevation <= 0:
                    # Ocean cell
                    risk_score = 0.0
                    risk_level = "OCEAN"
                    inundation_depth = 0.0
                else:
                    # Land cell
                    # Inundation depth = wave_height - elevation decay - distance decay
                    projected_inundation = effective_wave_height - (0.35 * elevation) - (0.04 * dist_to_shore)
                    inundation_depth = max(0.0, round(projected_inundation, 2))

                    if inundation_depth <= 0.01:
                        risk_score = 0.05
                        risk_level = "NO_RISK"
                    elif inundation_depth < 0.5:
                        risk_score = round(0.2 + inundation_depth * 0.3, 2)
                        risk_level = "LOW"
                    elif inundation_depth < 2.0:
                        risk_score = round(0.5 + (inundation_depth - 0.5) * 0.2, 2)
                        risk_level = "MODERATE"
                    elif inundation_depth < 4.0:
                        risk_score = round(0.8 + (inundation_depth - 2.0) * 0.08, 2)
                        risk_level = "HIGH"
                    else:
                        risk_score = 1.0
                        risk_level = "CRITICAL"

                row.append({
                    "x": x,
                    "y": y,
                    "elevation_m": elevation,
                    "inundation_depth_m": inundation_depth,
                    "risk_score": min(1.0, risk_score),
                    "risk_level": risk_level
                })
            risk_grid.append(row)

        return risk_grid

    def get_current_twin_state(self) -> Dict[str, Any]:
        """Fuses latest sensor stream into synchronized digital twin state."""
        sensor_snapshot = sim_engine.get_latest_snapshot()
        risk_grid = digital_twin_service.compute_inundation_risk_grid(sensor_snapshot)

        # High risk zone count
        high_risk_cells = 0
        critical_risk_cells = 0
        max_inundation = 0.0

        for row in risk_grid:
            for cell in row:
                if cell["risk_level"] in ["HIGH", "CRITICAL"]:
                    high_risk_cells += 1
                if cell["risk_level"] == "CRITICAL":
                    critical_risk_cells += 1
                if cell["inundation_depth_m"] > max_inundation:
                    max_inundation = cell["inundation_depth_m"]

        twin_state = {
            "timestamp": time.time(),
            "fused_sensors": sensor_snapshot["sensors"],
            "event_params": sensor_snapshot["event_params"],
            "is_event_active": sensor_snapshot["is_event_active"],
            "summary": {
                "max_inundation_depth_m": max_inundation,
                "high_risk_cells_count": high_risk_cells,
                "critical_risk_cells_count": critical_risk_cells,
                "overall_threat_active": high_risk_cells > 5 or sensor_snapshot["is_event_active"]
            },
            "risk_grid": risk_grid
        }
        return twin_state

    def record_snapshot(self, twin_state: Dict[str, Any]):
        """Persists snapshot into memory history buffer for audit/replay."""
        # Store compressed snapshot
        compact_snapshot = {
            "timestamp": twin_state["timestamp"],
            "is_event_active": twin_state["is_event_active"],
            "max_inundation": twin_state["summary"]["max_inundation_depth_m"],
            "high_risk_cells": twin_state["summary"]["high_risk_cells_count"],
            "sensors": twin_state["fused_sensors"]
        }
        self.snapshots_history.append(compact_snapshot)
        if len(self.snapshots_history) > 300: # Keep last 300 snapshots (~5 mins at 1s rate)
            self.snapshots_history.pop(0)

digital_twin_service = DigitalTwinService()
