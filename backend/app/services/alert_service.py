"""
Multi-channel alert dispatch: SMS (Twilio), Push (Firebase Cloud Messaging),
and real-time WebSocket broadcast to the dashboard.

Trigger condition (see app/services/pipeline.py):
    risk_level in {"HIGH", "SEVERE"}  -> SMS + Push + WebSocket
    risk_level == "MODERATE"          -> WebSocket only (dashboard banner)
    risk_level == "LOW"               -> no alert, logged only
"""
import logging
from app.config import settings
from app.websocket_manager import manager

logger = logging.getLogger("tsunami.alerts")

_twilio_client = None
_firebase_ready = False


def _get_twilio_client():
    global _twilio_client
    if _twilio_client is None and settings.twilio_account_sid:
        from twilio.rest import Client
        _twilio_client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    return _twilio_client


def _init_firebase():
    global _firebase_ready
    if _firebase_ready:
        return
    try:
        import firebase_admin
        from firebase_admin import credentials
        cred = credentials.Certificate(settings.firebase_credentials_json)
        firebase_admin.initialize_app(cred)
        _firebase_ready = True
    except Exception as e:
        logger.warning(f"Firebase not initialized ({e}). Push notifications disabled.")


def send_sms_alert(message: str) -> list[dict]:
    """Send SMS via Twilio to every number in ALERT_PHONE_NUMBERS."""
    client = _get_twilio_client()
    results = []
    if client is None:
        logger.warning("Twilio not configured — skipping SMS")
        return results

    for number in settings.alert_phone_number_list:
        try:
            msg = client.messages.create(
                body=message,
                from_=settings.twilio_from_number,
                to=number,
            )
            results.append({"recipient": number, "status": "SENT", "sid": msg.sid})
        except Exception as e:
            logger.error(f"Twilio SMS failed for {number}: {e}")
            results.append({"recipient": number, "status": "FAILED", "error": str(e)})
    return results


def send_push_alert(title: str, body: str, data: dict | None = None) -> dict:
    """Send a Firebase Cloud Messaging push notification to the alert topic."""
    _init_firebase()
    if not _firebase_ready:
        return {"status": "FAILED", "error": "firebase not configured"}
    try:
        from firebase_admin import messaging
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data={k: str(v) for k, v in (data or {}).items()},
            topic=settings.firebase_topic,
        )
        response = messaging.send(message)
        return {"status": "SENT", "message_id": response}
    except Exception as e:
        logger.error(f"Firebase push failed: {e}")
        return {"status": "FAILED", "error": str(e)}


async def broadcast_ws_alert(payload: dict):
    await manager.broadcast(payload)


async def dispatch_alert(risk_level: str, earthquake: dict, prediction) -> dict:
    """
    Central alert trigger. Called by the ingestion pipeline after every
    new risk prediction. Returns a summary of what was dispatched.
    """
    place = earthquake.get("place", "Unknown location")
    mag = earthquake.get("magnitude")
    message = (
        f"[{risk_level}] Tsunami risk near {place}. "
        f"M{mag} earthquake detected. {prediction.explanation}"
    )

    summary = {"risk_level": risk_level, "channels": []}

    # Always push to connected dashboards in real time
    await broadcast_ws_alert({
        "type": "ALERT",
        "risk_level": risk_level,
        "risk_score": prediction.risk_score,
        "earthquake": earthquake,
        "message": message,
    })
    summary["channels"].append("WEBSOCKET")

    if risk_level in ("HIGH", "SEVERE"):
        sms_results = send_sms_alert(message)
        push_result = send_push_alert(
            title=f"⚠️ Tsunami {risk_level} Risk",
            body=message,
            data={"risk_level": risk_level, "place": place},
        )
        summary["sms"] = sms_results
        summary["push"] = push_result
        summary["channels"] += ["SMS", "PUSH"]

    logger.info(f"Alert dispatched: {summary['channels']} for {risk_level}")
    return summary
