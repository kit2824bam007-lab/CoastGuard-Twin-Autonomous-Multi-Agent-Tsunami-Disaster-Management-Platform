"""
Pydantic request/response schemas.
"""
from datetime import datetime
from pydantic import BaseModel, Field


class EarthquakeOut(BaseModel):
    id: str
    magnitude: float
    depth_km: float
    latitude: float
    longitude: float
    place: str
    source: str
    event_time: datetime
    is_offshore: bool

    class Config:
        from_attributes = True


class RiskPredictionOut(BaseModel):
    id: int
    earthquake_id: str
    risk_level: str
    risk_score: float
    model_version: str
    explanation: str | None = None
    predicted_at: datetime

    class Config:
        from_attributes = True


class AlertOut(BaseModel):
    id: int
    channel: str
    recipient: str | None
    message: str
    status: str
    sent_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class ManualPredictRequest(BaseModel):
    """Used for /predict-risk when testing with a manual earthquake payload."""
    magnitude: float = Field(..., ge=0, le=10)
    depth_km: float = Field(..., ge=0)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    is_offshore: bool = True


class RiskPredictionResult(BaseModel):
    risk_level: str
    risk_score: float
    explanation: str
    model_version: str


class TsunamiForecastOut(BaseModel):
    id: int
    earthquake_id: str
    station_name: str
    distance_km: float
    arrival_time_hours: float
    wave_height_m: float
    predicted_at: datetime

    class Config:
        from_attributes = True


class SensorStationOut(BaseModel):
    id: str
    name: str
    type: str
    latitude: float
    longitude: float
    status: str

    class Config:
        from_attributes = True


class SensorReadingOut(BaseModel):
    id: int
    station_id: str
    timestamp: datetime
    water_level_m: float
    anomaly_detected: bool

    class Config:
        from_attributes = True


class CommandOverviewOut(BaseModel):
    event_id: str
    place: str
    digital_twin_status: str
    response_priority: str
    telemetry_confidence: float
    station_count: int
    sensor_confirmed: bool
    risk_level: str
    risk_score: float


class SwarmAgentOut(BaseModel):
    role: str
    owner: str
    mission: str
    priority: str


class SwarmPlanOut(BaseModel):
    event_id: str
    command_mode: str
    decision_summary: str
    place: str
    magnitude: float
    risk_level: str
    risk_score: float
    agents: list[SwarmAgentOut]
