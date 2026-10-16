"""
Real-time earthquake ingestion from the USGS Earthquake Hazards Program API.

Docs: https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php
Feed used (configurable in .env): significant_week.geojson
Other useful feeds:
  - all_hour.geojson        (every quake, last hour)
  - 2.5_day.geojson         (M2.5+, last day)
  - significant_week.geojson (M-significant events, last 7 days) <- good tsunami-relevant default

Sample response (GeoJSON FeatureCollection):
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "mag": 7.1, "place": "94 km SE of Kirakira, Solomon Islands",
        "time": 1717000000000, "tsunami": 1, "sig": 780, "type": "earthquake"
      },
      "geometry": { "type": "Point", "coordinates": [161.99, -11.03, 35.0] },
      "id": "us7000example"
    }
  ]
}
Note: geometry.coordinates = [longitude, latitude, depth_km]
      properties.tsunami = 1 means USGS already flagged tsunami potential.
"""
import logging
from datetime import datetime, timezone
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import settings

logger = logging.getLogger("tsunami.usgs")


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def fetch_usgs_feed() -> list[dict]:
    """Fetch and normalize the latest earthquake events from USGS."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(settings.usgs_feed_url)
        resp.raise_for_status()
        data = resp.json()

    events = []
    for feature in data.get("features", []):
        props = feature.get("properties", {})
        geom = feature.get("geometry", {})
        coords = geom.get("coordinates", [None, None, None])
        if coords[0] is None:
            continue

        lon, lat = coords[0], coords[1]
        depth = float(coords[2]) if coords[2] is not None else 0.0
        mag = float(props.get("mag")) if props.get("mag") is not None else 0.0
        events.append({
            "id": feature.get("id"),
            "magnitude": mag,
            "depth_km": depth,
            "latitude": float(lat),
            "longitude": float(lon),
            "place": props.get("place", "Unknown"),
            "source": "USGS",
            "event_time": datetime.fromtimestamp(props.get("time", 0) / 1000, tz=timezone.utc),
            "usgs_tsunami_flag": bool(props.get("tsunami", 0)),
            "raw_payload": feature,
        })
    logger.info(f"Fetched {len(events)} earthquake events from USGS")
    return events
