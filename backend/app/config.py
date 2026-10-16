"""
Centralized configuration loaded from environment variables (.env).
"""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    app_env: str = "development"
    log_level: str = "INFO"

    database_url: str = "postgresql+asyncpg://tsunami_user:tsunami_pass@localhost:5432/tsunami_db"

    usgs_feed_url: str = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_week.geojson"
    noaa_tsunami_atom_url: str = "https://www.tsunami.gov/events/xml/PAAQAtom.xml"
    poll_interval_seconds: int = 60

    min_magnitude_for_alert: float = 6.5
    max_depth_km_for_high_risk: float = 70.0

    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_from_number: str = ""
    alert_phone_numbers: str = ""  # comma-separated

    firebase_credentials_json: str = "./firebase-service-account.json"
    firebase_topic: str = "tsunami-alerts"

    redis_url: str = "redis://localhost:6379/0"
    redis_host: str = "localhost"
    redis_port: int = 6379

    mqtt_broker_host: str = "localhost"
    mqtt_broker_port: int = 1883

    api_key: str = "change_me"
    cors_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=[BACKEND_ENV_FILE, Path(__file__).resolve().parent.parent.parent / ".env"],
        extra="ignore"
    )

    @property
    def alert_phone_number_list(self) -> list[str]:
        return [p.strip() for p in self.alert_phone_numbers.split(",") if p.strip()]

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
