"""
CoastGuard Twin — FastAPI Main Application Entrypoint
Provides REST endpoints and WebSocket telemetry streaming for all 5 layers:
Layer 1: Sensing & Data Simulation
Layer 2: Digital Twin Synchronization
Layer 3: Swarm Intelligence Coordination
Layer 4: Metaverse Visualization Backend
Layer 5: Decision Support & ML Hazard Classification
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.services.data_sim_engine import sim_engine
from app.services.digital_twin import digital_twin_service
from app.services.swarm_engine import swarm_engine
from app.services.ml_classifier import ml_classifier
from app.services.benchmark_service import benchmark_service
from app.services.mqtt_service import mqtt_service
from app.database import init_db

from app.routers import sensors, twin, swarm, alerts, metrics, live_data, authority, federated, replay, data, predict, command

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("coastguard_twin.main")

# WebSocket Connection Manager
class TelemetryConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)

ws_manager = TelemetryConnectionManager()
sim_task: asyncio.Task = None

async def continuous_simulation_loop():
    """Background loop running at 1 Hz tick rate."""
    logger.info("Starting continuous 1 Hz simulation tick loop...")
    while True:
        try:
            # 1. Tick Sensor Simulation
            sensor_snapshot = sim_engine.tick()

            # 2. Synchronize Digital Twin
            twin_state = digital_twin_service.get_current_twin_state()
            digital_twin_service.record_snapshot(twin_state)

            # 3. Step Swarm Movement & Mesh Topology
            topology = swarm_engine.tick_pso_and_pathfinding(twin_state["risk_grid"])

            # 4. Infer ML Hazard Severity
            p_wave = sensor_snapshot["sensors"]["seismic"]["p_wave"]
            s_wave = sensor_snapshot["sensors"]["seismic"]["s_wave"]
            buoy = sensor_snapshot["sensors"]["dart_buoy"]["sea_level_anomaly_m"]
            shore = sensor_snapshot["sensors"]["shoreline_camera"]["state"]
            max_inundation = twin_state["summary"]["max_inundation_depth_m"]
            dist_km = sensor_snapshot["event_params"]["distance_km"]

            classification = ml_classifier.predict(p_wave, s_wave, buoy, shore, max_inundation, dist_km)

            # 5. Broadcast synchronized payload over WebSocket
            payload = {
                "type": "TELEMETRY_UPDATE",
                "timestamp": sensor_snapshot["timestamp"],
                "is_event_active": sensor_snapshot["is_event_active"],
                "sensors": sensor_snapshot["sensors"],
                "seismic_history": sensor_snapshot["history"]["seismic"],
                "buoy_history": sensor_snapshot["history"]["buoy"],
                "twin_summary": twin_state["summary"],
                "swarm": {
                    "agents": [a.to_dict() for a in swarm_engine.agents.values()],
                    "topology": topology
                },
                "hazard_classification": classification
            }

            await ws_manager.broadcast(payload)
            mqtt_service.publish_telemetry(payload)
            await asyncio.sleep(1.0)
        except asyncio.CancelledError:
            logger.info("Simulation loop cancelled.")
            break
        except Exception as e:
            logger.error(f"Error in simulation tick: {e}", exc_info=True)
            await asyncio.sleep(1.0)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global sim_task
    logger.info("Initializing CoastGuard Twin Backend Platform...")
    
    # 1. Initialize Database Schema (if DB container/service is accessible)
    try:
        await init_db()
        logger.info("Database schema initialized successfully.")
    except Exception as db_err:
        logger.warning(f"Database schema initialization deferred/skipped: {db_err}")

    # 2. Start MQTT Client Integration
    mqtt_service.start()

    # 3. Start 1 Hz simulation background loop
    sim_task = asyncio.create_task(continuous_simulation_loop())
    yield
    logger.info("Shutting down CoastGuard Twin Backend services...")
    if sim_task:
        sim_task.cancel()
    mqtt_service.stop()

app = FastAPI(
    title="CoastGuard Twin — Autonomous Disaster Management Platform",
    description="Simulated closed-loop Digital Twin + Swarm Intelligence + Metaverse platform",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Router Layers
app.include_router(sensors.router)
app.include_router(sensors.legacy_sensors_router)
app.include_router(twin.router)
app.include_router(swarm.router)
app.include_router(alerts.router)
app.include_router(metrics.router)
app.include_router(live_data.router)
app.include_router(authority.router)
app.include_router(federated.router)
app.include_router(replay.router)
app.include_router(data.router)
app.include_router(predict.router)
app.include_router(command.router)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "CoastGuard Twin Platform Engine",
        "tick_count": sim_engine.tick_count,
        "active_ws_clients": len(ws_manager.active_connections),
        "mqtt_connected": mqtt_service.is_connected
    }

@app.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection open and listen for any incoming command triggers
            data = await websocket.receive_json()
            if data.get("action") == "TRIGGER_EVENT":
                mag = float(data.get("magnitude", 7.8))
                dist = float(data.get("distance_km", 45.0))
                sim_engine.trigger_event(mag, dist)
            elif data.get("action") == "RESET":
                sim_engine.reset_simulation()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)
