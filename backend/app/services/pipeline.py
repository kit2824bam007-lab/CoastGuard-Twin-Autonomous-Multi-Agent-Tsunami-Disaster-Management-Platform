"""
End-to-end ingestion pipeline, run on a schedule (APScheduler) and also
callable on-demand from the /fetch-data route.

Step-by-step data flow:
  1. Fetch latest events from USGS
  2. Fetch active bulletins from NOAA
  3. For each NEW earthquake (not already in DB):
       a. Persist to `earthquakes` table
       b. Run risk model -> persist to `risk_predictions` table
       c. If risk_level requires it -> dispatch_alert() (SMS/Push/WS)
"""
import logging
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.orm import Earthquake, RiskPrediction, TsunamiForecast
from app.services.usgs_service import fetch_usgs_feed
from app.services.noaa_service import fetch_active_noaa_bulletins
from app.services.risk_model import get_active_risk_model, RuleBasedRiskModel
from app.services.wave_model import generate_tsunami_forecasts
from app.services.alert_service import dispatch_alert

logger = logging.getLogger("tsunami.pipeline")
risk_model = get_active_risk_model()


async def run_ingestion_cycle() -> dict:
    events = await fetch_usgs_feed()
    bulletins = await fetch_active_noaa_bulletins()
    active_bulletin = len(bulletins) > 0

    new_count = 0
    alerts_sent = 0

    async with AsyncSessionLocal() as session:
        for event in events:
            existing = await session.get(Earthquake, event["id"])
            if existing:
                continue  # already processed

            from app.services.geo_utils import is_offshore_coordinate
            is_off = is_offshore_coordinate(event["longitude"], event["latitude"])
            eq = Earthquake(
                id=event["id"],
                magnitude=event["magnitude"] or 0.0,
                depth_km=event["depth_km"] or 0.0,
                latitude=event["latitude"],
                longitude=event["longitude"],
                place=event["place"],
                source=event["source"],
                event_time=event["event_time"],
                is_offshore=is_off,
                raw_payload=str(event["raw_payload"]),
            )
            session.add(eq)
            await session.flush()
            new_count += 1

            # 1. Simulate real-time sensor measurements
            from app.services.sensor_service import simulate_readings_for_earthquake, confirm_tsunami_anomaly
            await simulate_readings_for_earthquake(
                session, eq.id, eq.latitude, eq.longitude, eq.magnitude, eq.depth_km, eq.is_offshore, eq.event_time
            )

            # 2. Run model predictions
            result = risk_model.predict(
                magnitude=eq.magnitude,
                depth_km=eq.depth_km,
                latitude=eq.latitude,
                longitude=eq.longitude,
                is_offshore=eq.is_offshore,
                usgs_tsunami_flag=event.get("usgs_tsunami_flag", False),
                active_noaa_bulletin=active_bulletin,
            ) if isinstance(risk_model, RuleBasedRiskModel) else risk_model.predict(
                magnitude=eq.magnitude, depth_km=eq.depth_km,
                latitude=eq.latitude, longitude=eq.longitude, is_offshore=eq.is_offshore,
            )

            # 3. Telemetry Verification: verify tsunami via offshore sensors
            confirmed, sensor_explanation = await confirm_tsunami_anomaly(session, eq.latitude, eq.longitude)
            if confirmed:
                result.explanation += f"; {sensor_explanation}"
                if result.risk_level in ("HIGH", "SEVERE") or eq.magnitude >= 7.2:
                    result.risk_level = "SEVERE"
                    result.risk_score = max(result.risk_score, 0.95)
                    result.explanation += " (Tsunami verified by deep ocean buoy anomaly)"

            prediction = RiskPrediction(
                earthquake_id=eq.id,
                risk_level=result.risk_level,
                risk_score=result.risk_score,
                model_version=result.model_version,
                explanation=result.explanation,
            )
            session.add(prediction)

            # Generate and archive physical wave forecasts
            forecast_results = generate_tsunami_forecasts(
                eq_lat=eq.latitude,
                eq_lon=eq.longitude,
                magnitude=eq.magnitude,
                depth_km=eq.depth_km,
                is_offshore=eq.is_offshore
            )
            for f in forecast_results:
                tf = TsunamiForecast(
                    earthquake_id=eq.id,
                    station_name=f["station_name"],
                    distance_km=f["distance_km"],
                    arrival_time_hours=f["arrival_time_hours"],
                    wave_height_m=f["wave_height_m"]
                )
                session.add(tf)

            await session.commit()

            if result.risk_level != "LOW":
                await dispatch_alert(
                    result.risk_level,
                    earthquake={
                        "id": eq.id, "magnitude": eq.magnitude, "place": eq.place,
                        "latitude": eq.latitude, "longitude": eq.longitude,
                    },
                    prediction=result,
                )
                alerts_sent += 1

    logger.info(f"Ingestion cycle complete: {new_count} new events, {alerts_sent} alerts sent")
    return {"new_events": new_count, "alerts_sent": alerts_sent, "active_noaa_bulletins": len(bulletins)}
