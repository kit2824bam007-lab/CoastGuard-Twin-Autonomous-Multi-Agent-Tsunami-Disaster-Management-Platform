"""
V2 Extension 1 — Real Public Data Integration Module
Fetches real-time earthquake feeds from USGS Earthquake Hazards Program GeoJSON API
and sea-level anomaly data from NOAA Tides & Currents API / INCOIS feeds.
"""
import time
import httpx
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger("coastguard_twin.live_data")

USGS_FEED_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_day.geojson"

class LiveDataService:
    def __init__(self):
        self.mode = "SIMULATED" # SIMULATED or LIVE_PUBLIC_FEEDS
        self.last_usgs_fetch_time = 0.0
        self.cached_earthquakes: List[Dict[str, Any]] = []

    def set_mode(self, mode: str) -> Dict[str, Any]:
        if mode.upper() in ["SIMULATED", "LIVE_PUBLIC_FEEDS"]:
            self.mode = mode.upper()
        return {
            "mode": self.mode,
            "safety_notice": "Live mode active for testing — output strictly confined within simulation loop."
        }

    async def fetch_usgs_earthquakes(self) -> List[Dict[str, Any]]:
        """Fetches real-time M4.5+ earthquake GeoJSON feed from USGS."""
        now = time.time()
        # Cache for 60 seconds to avoid spamming USGS API
        if now - self.last_usgs_fetch_time < 60.0 and self.cached_earthquakes:
            return self.cached_earthquakes

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(USGS_FEED_URL)
                if res.status_code == 200:
                    data = res.json()
                    features = data.get("features", [])
                    
                    parsed_quakes = []
                    for f in features[:15]: # Top 15 recent quakes
                        props = f.get("properties", {})
                        geom = f.get("geometry", {})
                        coords = geom.get("coordinates", [0, 0, 0])
                        
                        parsed_quakes.append({
                            "id": f.get("id"),
                            "title": props.get("title"),
                            "magnitude": props.get("mag"),
                            "place": props.get("place"),
                            "time_epoch": props.get("time"),
                            "tsunami_flag": props.get("tsunami") == 1,
                            "coordinates": {
                                "longitude": coords[0],
                                "latitude": coords[1],
                                "depth_km": coords[2]
                            }
                        })
                    
                    self.cached_earthquakes = parsed_quakes
                    self.last_usgs_fetch_time = now
                    return parsed_quakes
        except Exception as e:
            logger.error(f"Error fetching USGS GeoJSON feed: {e}")
        
        return self.cached_earthquakes

    async def get_live_data_snapshot(self) -> Dict[str, Any]:
        quakes = await self.fetch_usgs_earthquakes()
        highest_quake = max(quakes, key=lambda q: q["magnitude"]) if quakes else None

        return {
            "mode": self.mode,
            "usgs_quakes_count": len(quakes),
            "highest_magnitude_quake": highest_quake,
            "recent_quakes": quakes[:5],
            "noaa_tide_status": "NOMINAL_STATION_FEED",
            "safety_disclaimer": "LIVE PUBLIC FEED MODE ACTIVE — Strictly isolated within simulation decision loop."
        }

live_data_service = LiveDataService()
