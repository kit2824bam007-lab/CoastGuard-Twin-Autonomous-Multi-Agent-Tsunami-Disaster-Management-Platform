"""
Offshore buoy (DART) and coastal tide gauge sensor integration service.
"""
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from app.models.orm import SensorStation, SensorReading
from app.services.geo_utils import haversine_distance
from app.services.wave_model import predict_wave_metrics

logger = logging.getLogger("tsunami.sensors")

# Core global sensor registry
DEFAULT_STATIONS = [
    {"id": "DART-21418", "name": "NW Pacific DART Buoy 21418", "type": "DART", "latitude": 38.7, "longitude": 148.7},
    {"id": "DART-46407", "name": "Aleutian DART Buoy 46407", "type": "DART", "latitude": 52.6, "longitude": -168.9},
    {"id": "DART-32412", "name": "Peru-Chile DART Buoy 32412", "type": "DART", "latitude": -18.0, "longitude": -86.4},
    {"id": "TIDE-Tokyo", "name": "Tokyo Harbour Tide Station", "type": "TIDE", "latitude": 35.6, "longitude": 139.7},
    {"id": "TIDE-Hilo", "name": "Hilo Bay Tide Station", "type": "TIDE", "latitude": 19.7, "longitude": -155.1},
    {"id": "TIDE-BandaAceh", "name": "Banda Aceh Coastal Tide Gauge", "type": "TIDE", "latitude": 5.5, "longitude": 95.3},
    {"id": "TIDE-Rakata", "name": "Rakata Island Water Level Gauge", "type": "TIDE", "latitude": -6.155, "longitude": 105.427}
]


async def seed_sensor_stations(session) -> int:
    """Pre-seeds the list of DART buoys and tide gauges on database initialization."""
    stmt = select(SensorStation)
    result = await session.execute(stmt)
    existing = result.scalars().all()
    if len(existing) > 0:
        return 0

    seeded = 0
    for s in DEFAULT_STATIONS:
        station = SensorStation(
            id=s["id"],
            name=s["name"],
            type=s["type"],
            latitude=s["latitude"],
            longitude=s["longitude"],
            status="ACTIVE"
        )
        session.add(station)
        seeded += 1

    await session.commit()
    logger.info(f"Seeded {seeded} sensor stations into database")
    return seeded


async def simulate_readings_for_earthquake(
    session,
    eq_id: str,
    eq_lat: float,
    eq_lon: float,
    magnitude: float,
    depth_km: float,
    is_offshore: bool,
    event_time: datetime
):
    """
    Simulates the physical propagation of a tsunami wave to all registered stations,
    writing telemetry records (baseline + wave transit peaks) into the database.
    """
    stmt = select(SensorStation)
    result = await session.execute(stmt)
    stations = result.scalars().all()

    reading_count = 0
    for station in stations:
        # 1. Compute wave propagation details for this station using physical model
        dist_km, travel_time_hours, wave_height_m = predict_wave_metrics(
            station.latitude, station.longitude,
            eq_lat, eq_lon,
            magnitude, depth_km, is_offshore
        )

        # Ensure event_time is timezone aware
        if event_time.tzinfo is None:
            event_time = event_time.replace(tzinfo=timezone.utc)

        # 2. Write baseline measurements (before the wave arrives)
        baselines = [
            (-60, 0.05),
            (-30, -0.02),
            (0, 0.02)
        ]
        for offset_min, baseline_offset in baselines:
            ts = event_time + timedelta(minutes=offset_min)
            reading = SensorReading(
                station_id=station.id,
                timestamp=ts,
                water_level_m=baseline_offset,
                anomaly_detected=False
            )
            session.add(reading)
            reading_count += 1

        # 3. Write simulated anomaly wave profiles if a wave was generated
        if wave_height_m >= 0.05:
            arrival_dt = event_time + timedelta(hours=travel_time_hours)

            # Build a wave train profile (drawdown precursor -> peak -> damping)
            wave_profile = [
                (-5, -0.15 * wave_height_m, False),                       # precursor drawdown
                (0, wave_height_m, True),                                 # tsunami arrival peak
                (10, 0.6 * wave_height_m, True),                          # subsequent crest
                (30, 0.2 * wave_height_m, False),                         # decaying wave tail
                (60, 0.05 * wave_height_m, False)
            ]

            for offset_min, factor, is_anomaly in wave_profile:
                ts = arrival_dt + timedelta(minutes=offset_min)
                reading = SensorReading(
                    station_id=station.id,
                    timestamp=ts,
                    water_level_m=round(factor, 3),
                    anomaly_detected=is_anomaly
                )
                session.add(reading)
                reading_count += 1

    await session.commit()
    logger.info(f"Simulated {reading_count} sensor telemetry readings for event {eq_id}")


async def confirm_tsunami_anomaly(session, eq_lat: float, eq_lon: float, max_dist_km: float = 3000.0) -> tuple[bool, str]:
    """
    Evaluates nearby active buoy and tide gauge readings to confirm tsunami activity.
    Returns: (confirmed: bool, reasoning_text: str)
    """
    # Find stations within distance
    stmt = select(SensorStation).where(SensorStation.status == "ACTIVE")
    result = await session.execute(stmt)
    stations = result.scalars().all()

    matching_stations = []
    for s in stations:
        dist = haversine_distance(eq_lat, eq_lon, s.latitude, s.longitude)
        if dist <= max_dist_km:
            matching_stations.append((s, dist))

    if not matching_stations:
        return False, "No active sensor stations within telemetry confirmation field"

    # Search for any recent readings that recorded positive anomalies (within last 24h)
    time_limit = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(hours=24)
    confirmed_stations = []

    for s, dist in matching_stations:
        stmt_readings = (
            select(SensorReading)
            .where(SensorReading.station_id == s.id)
            .where(SensorReading.timestamp >= time_limit)
            .where(SensorReading.anomaly_detected == True)
        )
        res_readings = await session.execute(stmt_readings)
        readings = res_readings.scalars().all()

        if len(readings) > 0:
            max_level = max(r.water_level_m for r in readings)
            confirmed_stations.append(f"{s.id} (elev: {max_level:.2f}m at {dist:.0f}km)")

    if len(confirmed_stations) > 0:
        explanation = "Tsunami generation confirmed by telemetries: " + ", ".join(confirmed_stations)
        return True, explanation

    return False, "Telemetry channels scanning normal: no offshore buoy anomalies detected"
