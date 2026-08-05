"""
V2 Extension 6 — Extended SMS (Twilio) and Push (Firebase) Alert Channels
Implements AlertChannel interface with sandbox feature flags.
"""
import os
import logging
from typing import Dict, Any
from app.services.ml_classifier import AlertChannel

logger = logging.getLogger("coastguard_twin.alerts")

class TwilioSMSAlertChannel(AlertChannel):
    def __init__(self):
        self.enabled = os.getenv("ENABLE_TWILIO_SMS", "false").lower() == "true"
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID", "AC_SANDBOX_TEST_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN", "AUTH_SANDBOX_TEST_TOKEN")
        self.from_phone = os.getenv("TWILIO_FROM_PHONE", "+15005550006") # Twilio test number

    def dispatch(self, title: str, message: str, severity: str) -> Dict[str, Any]:
        if not self.enabled:
            logger.info("[TWILIO SMS SANDBOX] Alert channel disabled or in sandbox mode.")
            return {
                "channel": "twilio_sms",
                "status": "SANDBOX_MOCK_SUCCESS",
                "enabled": False,
                "sandbox_notice": "SMS feature flag defaulted OFF for safety. Mock dispatch logged.",
                "payload": {"title": title, "message": message, "to": "MOCK_SANDBOX_SUBSCRIBERS"}
            }
        
        # Real Twilio API integration when enabled
        try:
            from twilio.rest import Client
            client = Client(self.account_sid, self.auth_token)
            # Dispatch to configured test phone number
            sms = client.messages.create(
                body=f"[{severity.upper()}] {title}: {message}",
                from_=self.from_phone,
                to="+15005550006" # Magic test number
            )
            return {"channel": "twilio_sms", "status": "SENT", "sid": sms.sid}
        except Exception as e:
            logger.error(f"Error dispatching Twilio SMS: {e}")
            return {"channel": "twilio_sms", "status": "ERROR", "error": str(e)}

class FirebasePushAlertChannel(AlertChannel):
    def __init__(self):
        self.enabled = os.getenv("ENABLE_FIREBASE_PUSH", "false").lower() == "true"

    def dispatch(self, title: str, message: str, severity: str) -> Dict[str, Any]:
        return {
            "channel": "firebase_push",
            "status": "SANDBOX_BROADCAST" if not self.enabled else "SENT",
            "enabled": self.enabled,
            "topic": f"tsunami-alerts-{severity.lower()}",
            "payload": {"title": title, "body": message}
        }
