"""
V2 Extension 7 — Historical Replay & Responder Training Mode
Stores and replays past simulated event timelines frame-by-frame
for after-action review and responder XR training exercises.
"""
import time
from typing import Dict, List, Any, Optional

class ReplayService:
    def __init__(self):
        self.recorded_sessions: Dict[str, Dict[str, Any]] = {}
        self._generate_preset_demo_session()

    def _generate_preset_demo_session(self):
        """Generates a preset historical tsunami event timeline (M7.8 Bay of Bengal Event)."""
        session_id = "SESSION-M7.8-DEMO"
        frames = []
        
        # 30 seconds simulation timeline (1 frame per sec)
        for t in range(30):
            is_active = t >= 5
            mag = 7.8 if is_active else 0.0
            anomaly = round(0.05 + (0.15 * (t - 5)) if is_active else 0.05, 2)
            
            frames.append({
                "frame_index": t,
                "timestamp_rel_sec": t,
                "is_event_active": is_active,
                "earthquake_magnitude": mag,
                "buoy_sea_level_anomaly_m": min(3.2, max(0.05, anomaly)),
                "shoreline_state": "RECEDING" if 5 <= t < 15 else ("SURGING" if t >= 15 else "NORMAL"),
                "hazard_class": "SEVERE" if t >= 15 else ("WARNING" if t >= 8 else ("WATCH" if t >= 5 else "NO_THREAT")),
                "active_swarm_count": 9 if t < 20 else 8, # Agent loss at t=20
                "max_inundation_m": round(max(0.0, (anomaly - 0.2)), 2)
            })

        self.recorded_sessions[session_id] = {
            "session_id": session_id,
            "title": "Historical Scenario: 2026 M7.8 Coastal Inundation Event",
            "duration_sec": 30,
            "recorded_at": "2026-08-04T12:00:00Z",
            "frames_count": len(frames),
            "frames": frames
        }

    def list_sessions(self) -> List[Dict[str, Any]]:
        return [
            {
                "session_id": s["session_id"],
                "title": s["title"],
                "duration_sec": s["duration_sec"],
                "recorded_at": s["recorded_at"],
                "frames_count": s["frames_count"]
            }
            for s in self.recorded_sessions.values()
        ]

    def get_session_timeline(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self.recorded_sessions.get(session_id)

replay_service = ReplayService()
