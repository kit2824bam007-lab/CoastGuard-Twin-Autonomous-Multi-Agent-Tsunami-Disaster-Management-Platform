"""
Layer 1 — Sensing & Data Acquisition Engine
Simulates continuous real-time streams for:
1. Seismic waveforms (P/S waves, event injection)
2. DART buoy sea-level anomalies (tsunami wave packet propagation)
3. 50x50 Bathymetry & elevation grid (synthetic coastline)
4. Coastal camera shoreline state (NORMAL / RECEDING / SURGING)
"""
import time
import math
import asyncio
import numpy as np
from typing import Dict, List, Any, Optional

GRID_SIZE = 50

class DataSimEngine:
    def __init__(self):
        self.tick_count = 0
        self.is_event_active = False
        self.event_start_time = 0.0
        self.event_magnitude = 7.5
        self.event_distance_km = 50.0

        # Sensor states
        self.seismic_p_wave = 0.02
        self.seismic_s_wave = 0.05
        self.buoy_anomaly_meters = 0.05
        self.shoreline_state = "NORMAL" # NORMAL, RECEDING, SURGING

        # Waveform history buffer (last 60 seconds)
        self.seismic_history: List[Dict[str, float]] = []
        self.buoy_history: List[Dict[str, float]] = []

        # Generate static bathymetry grid once (50x50)
        # x=0 is deep ocean (-100m), x=20 is coastline (0m), x=49 is inland (+80m)
        self.bathymetry_grid = np.zeros((GRID_SIZE, GRID_SIZE), dtype=float)
        self._generate_bathymetry()

    def _generate_bathymetry(self):
        """Generates a realistic 50x50 coastal bathymetry grid with ocean shelf, slope, and land elevation."""
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                # Add slight coastline curvature using sine wave
                coast_x = 20.0 + 3.0 * math.sin(y / 5.0)
                dist_from_coast = x - coast_x
                
                if dist_from_coast < 0:
                    # Underwater (depth negative in meters)
                    # Steeper shelf near shore, deeper further out
                    depth = dist_from_coast * 3.5 - 5.0 * math.cos(y / 8.0)
                    self.bathymetry_grid[y, x] = round(max(-200.0, depth), 2)
                else:
                    # Elevation above sea level (positive in meters)
                    elevation = dist_from_coast * 2.2 + 2.0 * math.sin(x / 4.0) * math.cos(y / 4.0)
                    self.bathymetry_grid[y, x] = round(min(120.0, elevation), 2)

    def trigger_event(self, magnitude: float = 7.8, distance_km: float = 45.0):
        """Injects a simulated earthquake event with wave propagation."""
        self.is_event_active = True
        self.event_start_time = time.time()
        self.event_magnitude = max(5.0, min(9.5, magnitude))
        self.event_distance_km = max(5.0, min(500.0, distance_km))
        self.shoreline_state = "RECEDING"

    def reset_simulation(self):
        self.is_event_active = False
        self.shoreline_state = "NORMAL"
        self.buoy_anomaly_meters = 0.05
        self.seismic_p_wave = 0.02
        self.seismic_s_wave = 0.05

    def tick(self) -> Dict[str, Any]:
        """Calculates current sensor readings for this tick."""
        self.tick_count += 1
        now = time.time()
        t = now - self.event_start_time if self.is_event_active else 0.0

        # Baseline ambient noise
        noise = np.random.normal(0, 0.01)

        if not self.is_event_active:
            self.seismic_p_wave = round(abs(0.02 * math.sin(self.tick_count * 0.5) + noise), 4)
            self.seismic_s_wave = round(abs(0.04 * math.cos(self.tick_count * 0.3) + noise), 4)
            self.buoy_anomaly_meters = round(abs(0.05 + 0.03 * math.sin(self.tick_count * 0.1) + noise), 3)
            self.shoreline_state = "NORMAL"
        else:
            # Earthquake wave physics
            # P wave arrives first (speed ~6 km/s), S wave second (~3.5 km/s)
            p_arrival = self.event_distance_km / 6.0
            s_arrival = self.event_distance_km / 3.5

            # Amplitude scales exponentially with magnitude and decays with distance
            peak_amp = (10 ** (self.event_magnitude - 6.0)) / math.sqrt(self.event_distance_km)

            p_amp = 0.0
            if t >= p_arrival:
                t_p = t - p_arrival
                p_amp = peak_amp * 0.4 * math.exp(-0.15 * t_p) * abs(math.sin(2.0 * math.pi * 3.0 * t_p))

            s_amp = 0.0
            if t >= s_arrival:
                t_s = t - s_arrival
                s_amp = peak_amp * 0.9 * math.exp(-0.08 * t_s) * abs(math.sin(2.0 * math.pi * 1.5 * t_s))

            self.seismic_p_wave = round(max(0.02, p_amp + abs(noise)), 4)
            self.seismic_s_wave = round(max(0.04, s_amp + abs(noise)), 4)

            # Tsunami wave speed in shallow water c = sqrt(g * d) ~ 15-30 m/s in shelf
            # Tsunami arrival at buoy (distance_km)
            tsunami_arrival = self.event_distance_km * 12.0 # seconds scale for simulation speed
            wave_peak_height = (10 ** (self.event_magnitude - 6.2)) * 1.2

            if t < tsunami_arrival:
                # Water draws back before wave arrival
                drawback = -0.3 * wave_peak_height * (t / tsunami_arrival)
                self.buoy_anomaly_meters = round(max(-2.5, drawback + noise), 3)
                self.shoreline_state = "RECEDING"
            elif t < tsunami_arrival + 40.0:
                # Wave surge
                t_surge = t - tsunami_arrival
                surge = wave_peak_height * (math.cosh((t_surge - 15.0) / 8.0) ** -2)
                self.buoy_anomaly_meters = round(max(0.1, surge + noise + 0.5), 3)
                self.shoreline_state = "SURGING"
            else:
                # Gradual dissipation
                t_decay = t - (tsunami_arrival + 40.0)
                decaying_wave = wave_peak_height * 0.3 * math.exp(-0.05 * t_decay) * abs(math.cos(t_decay * 0.2))
                self.buoy_anomaly_meters = round(max(0.05, decaying_wave + 0.1), 3)
                self.shoreline_state = "SURGING" if decaying_wave > 0.8 else "NORMAL"

        # Update histories
        timestamp = round(now, 2)
        self.seismic_history.append({
            "time": timestamp,
            "p_wave": self.seismic_p_wave,
            "s_wave": self.seismic_s_wave,
            "amplitude": round(self.seismic_p_wave + self.seismic_s_wave, 4)
        })
        self.buoy_history.append({
            "time": timestamp,
            "anomaly_meters": self.buoy_anomaly_meters
        })

        if len(self.seismic_history) > 60:
            self.seismic_history.pop(0)
        if len(self.buoy_history) > 60:
            self.buoy_history.pop(0)

        return self.get_latest_snapshot()

    def get_latest_snapshot(self) -> Dict[str, Any]:
        return {
            "timestamp": round(time.time(), 2),
            "tick": self.tick_count,
            "is_event_active": self.is_event_active,
            "event_params": {
                "magnitude": self.event_magnitude,
                "distance_km": self.event_distance_km,
                "start_time": self.event_start_time
            },
            "sensors": {
                "seismic": {
                    "p_wave": self.seismic_p_wave,
                    "s_wave": self.seismic_s_wave,
                    "combined_amplitude": round(self.seismic_p_wave + self.seismic_s_wave, 4)
                },
                "dart_buoy": {
                    "sea_level_anomaly_m": self.buoy_anomaly_meters,
                    "status": "ANOMALY_DETECTED" if self.buoy_anomaly_meters > 0.8 else "NOMINAL"
                },
                "shoreline_camera": {
                    "state": self.shoreline_state
                }
            },
            "history": {
                "seismic": self.seismic_history,
                "buoy": self.buoy_history
            }
        }

    def get_bathymetry_grid(self) -> List[List[float]]:
        return self.bathymetry_grid.tolist()

# Global engine instance
sim_engine = DataSimEngine()
