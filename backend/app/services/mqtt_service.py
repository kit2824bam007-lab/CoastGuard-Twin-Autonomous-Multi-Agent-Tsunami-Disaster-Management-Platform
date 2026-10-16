"""
Eclipse Mosquitto MQTT Broker Integration Service for CoastGuard Twin.
Publishes real-time telemetry and hazard alerts to MQTT topics,
and listens for remote emergency commands.
"""
import json
import logging
from typing import Any, Dict, Optional

from app.config import settings

logger = logging.getLogger("coastguard_twin.mqtt")

TOPIC_TELEMETRY = "coastguard/telemetry"
TOPIC_ALERTS = "coastguard/alerts"
TOPIC_COMMANDS = "coastguard/commands"


class MqttService:
    def __init__(self):
        self.client = None
        self.is_connected: bool = False
        self.host = settings.mqtt_broker_host
        self.port = settings.mqtt_broker_port

    def start(self):
        """Initializes and connects the MQTT client in background loop."""
        try:
            import paho.mqtt.client as mqtt

            # Compatibility with paho-mqtt v2 and v1
            if hasattr(mqtt, "CallbackAPIVersion"):
                self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            else:
                self.client = mqtt.Client()

            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message

            logger.info(f"Connecting to MQTT broker at {self.host}:{self.port}...")
            self.client.connect_async(self.host, self.port, keepalive=60)
            self.client.loop_start()
        except ImportError:
            logger.warning("paho-mqtt not installed. MQTT service operating in mock/offline mode.")
        except Exception as e:
            logger.warning(f"Could not connect to MQTT broker ({e}). Operating in standalone mode.")

    def stop(self):
        """Stops the MQTT client background loop and disconnects."""
        if self.client:
            try:
                self.client.loop_stop()
                self.client.disconnect()
                logger.info("MQTT client disconnected successfully.")
            except Exception as e:
                logger.debug(f"Error during MQTT shutdown: {e}")

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        rc_code = getattr(rc, "value", rc)
        if rc_code == 0:
            self.is_connected = True
            logger.info(f"Successfully connected to MQTT Broker ({self.host}:{self.port}).")
            client.subscribe(TOPIC_COMMANDS)
            logger.info(f"Subscribed to MQTT topic: {TOPIC_COMMANDS}")
        else:
            logger.warning(f"MQTT connection refused with result code: {rc}")

    def _on_disconnect(self, client, userdata, rc, properties=None):
        self.is_connected = False
        logger.info("MQTT client disconnected from broker.")

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            logger.info(f"Received MQTT command on {msg.topic}: {payload}")
            from app.services.data_sim_engine import sim_engine
            action = payload.get("action")
            if action == "TRIGGER_EVENT":
                mag = float(payload.get("magnitude", 7.8))
                dist = float(payload.get("distance_km", 45.0))
                sim_engine.trigger_event(mag, dist)
            elif action == "RESET":
                sim_engine.reset_simulation()
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")

    def publish_telemetry(self, payload: Dict[str, Any]):
        """Publishes 1 Hz fused digital twin + swarm telemetry to MQTT topic."""
        if self.client and self.is_connected:
            try:
                data_str = json.dumps(payload, default=str)
                self.client.publish(TOPIC_TELEMETRY, data_str, qos=0)
            except Exception as e:
                logger.debug(f"MQTT telemetry publish error: {e}")

    def publish_alert(self, alert_payload: Dict[str, Any]):
        """Publishes emergency evacuation alert to MQTT topic."""
        if self.client and self.is_connected:
            try:
                data_str = json.dumps(alert_payload, default=str)
                self.client.publish(TOPIC_ALERTS, data_str, qos=1)
                logger.info(f"Dispatched emergency alert to MQTT topic '{TOPIC_ALERTS}'")
            except Exception as e:
                logger.error(f"MQTT alert publish error: {e}")


mqtt_service = MqttService()
