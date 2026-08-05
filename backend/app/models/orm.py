"""
SQLAlchemy ORM models — mirrors database/schema.sql
"""
from datetime import datetime
from sqlalchemy import String, Float, DateTime, ForeignKey, Text, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Earthquake(Base):
    __tablename__ = "earthquakes"

    id: Mapped[str] = mapped_column(String, primary_key=True)          # USGS event id
    magnitude: Mapped[float] = mapped_column(Float)
    depth_km: Mapped[float] = mapped_column(Float)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    place: Mapped[str] = mapped_column(String)
    source: Mapped[str] = mapped_column(String, default="USGS")
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    is_offshore: Mapped[bool] = mapped_column(Boolean, default=False)
    raw_payload: Mapped[str] = mapped_column(Text, nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    risk_predictions: Mapped[list["RiskPrediction"]] = relationship(back_populates="earthquake")
    tsunami_forecasts: Mapped[list["TsunamiForecast"]] = relationship(back_populates="earthquake", cascade="all, delete-orphan")


class RiskPrediction(Base):
    __tablename__ = "risk_predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    earthquake_id: Mapped[str] = mapped_column(String, ForeignKey("earthquakes.id"))
    risk_level: Mapped[str] = mapped_column(String)      # LOW / MODERATE / HIGH / SEVERE
    risk_score: Mapped[float] = mapped_column(Float)     # 0.0 - 1.0
    model_version: Mapped[str] = mapped_column(String, default="rule-based-v1")
    explanation: Mapped[str] = mapped_column(Text, nullable=True)
    predicted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    earthquake: Mapped["Earthquake"] = relationship(back_populates="risk_predictions")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="risk_prediction")


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    risk_prediction_id: Mapped[int] = mapped_column(Integer, ForeignKey("risk_predictions.id"))
    channel: Mapped[str] = mapped_column(String)          # SMS / PUSH / WEBSOCKET
    recipient: Mapped[str] = mapped_column(String, nullable=True)
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String, default="PENDING")  # PENDING / SENT / FAILED
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    risk_prediction: Mapped["RiskPrediction"] = relationship(back_populates="alerts")


class TsunamiForecast(Base):
    __tablename__ = "tsunami_forecasts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    earthquake_id: Mapped[str] = mapped_column(String, ForeignKey("earthquakes.id"))
    station_name: Mapped[str] = mapped_column(String)
    distance_km: Mapped[float] = mapped_column(Float)
    arrival_time_hours: Mapped[float] = mapped_column(Float)
    wave_height_m: Mapped[float] = mapped_column(Float)
    predicted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    earthquake: Mapped["Earthquake"] = relationship(back_populates="tsunami_forecasts")


class SensorStation(Base):
    __tablename__ = "sensor_stations"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    type: Mapped[str] = mapped_column(String)  # 'DART' or 'TIDE'
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String, default="ACTIVE")

    readings: Mapped[list["SensorReading"]] = relationship(back_populates="station", cascade="all, delete-orphan")


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    station_id: Mapped[str] = mapped_column(String, ForeignKey("sensor_stations.id"))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    water_level_m: Mapped[float] = mapped_column(Float)
    anomaly_detected: Mapped[bool] = mapped_column(Boolean, default=False)

    station: Mapped["SensorStation"] = relationship(back_populates="readings")
