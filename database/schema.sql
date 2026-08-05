-- PostgreSQL schema for the Tsunami Early Warning System
-- Apply with: psql -U tsunami_user -d tsunami_db -f schema.sql
-- (SQLAlchemy's init_db() also auto-creates these tables on backend startup)

CREATE TABLE IF NOT EXISTS earthquakes (
    id              VARCHAR PRIMARY KEY,          -- USGS event id, e.g. "us7000example"
    magnitude       FLOAT NOT NULL,
    depth_km        FLOAT NOT NULL,
    latitude        FLOAT NOT NULL,
    longitude       FLOAT NOT NULL,
    place           VARCHAR NOT NULL,
    source          VARCHAR NOT NULL DEFAULT 'USGS',
    event_time      TIMESTAMPTZ NOT NULL,
    is_offshore     BOOLEAN NOT NULL DEFAULT FALSE,
    raw_payload     TEXT,
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS risk_predictions (
    id              SERIAL PRIMARY KEY,
    earthquake_id   VARCHAR NOT NULL REFERENCES earthquakes(id) ON DELETE CASCADE,
    risk_level      VARCHAR NOT NULL CHECK (risk_level IN ('LOW','MODERATE','HIGH','SEVERE')),
    risk_score      FLOAT NOT NULL CHECK (risk_score BETWEEN 0 AND 1),
    model_version   VARCHAR NOT NULL DEFAULT 'rule-based-v1',
    explanation     TEXT,
    predicted_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS alerts (
    id                  SERIAL PRIMARY KEY,
    risk_prediction_id  INTEGER NOT NULL REFERENCES risk_predictions(id) ON DELETE CASCADE,
    channel             VARCHAR NOT NULL CHECK (channel IN ('SMS','PUSH','WEBSOCKET')),
    recipient           VARCHAR,
    message             TEXT NOT NULL,
    status              VARCHAR NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING','SENT','FAILED')),
    sent_at             TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS tsunami_forecasts (
    id                  SERIAL PRIMARY KEY,
    earthquake_id       VARCHAR NOT NULL REFERENCES earthquakes(id) ON DELETE CASCADE,
    station_name        VARCHAR NOT NULL,
    distance_km         FLOAT NOT NULL,
    arrival_time_hours  FLOAT NOT NULL,
    wave_height_m       FLOAT NOT NULL,
    predicted_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sensor_stations (
    id                  VARCHAR PRIMARY KEY,          -- e.g. "DART-21418"
    name                VARCHAR NOT NULL,
    type                VARCHAR NOT NULL,             -- 'DART' or 'TIDE'
    latitude            FLOAT NOT NULL,
    longitude           FLOAT NOT NULL,
    status              VARCHAR NOT NULL DEFAULT 'ACTIVE'
);

CREATE TABLE IF NOT EXISTS sensor_readings (
    id                  SERIAL PRIMARY KEY,
    station_id          VARCHAR NOT NULL REFERENCES sensor_stations(id) ON DELETE CASCADE,
    timestamp           TIMESTAMPTZ NOT NULL,
    water_level_m       FLOAT NOT NULL,
    anomaly_detected    BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_earthquakes_event_time ON earthquakes(event_time DESC);
CREATE INDEX IF NOT EXISTS idx_earthquakes_location ON earthquakes(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_risk_predictions_earthquake ON risk_predictions(earthquake_id);
CREATE INDEX IF NOT EXISTS idx_risk_predictions_level ON risk_predictions(risk_level);
CREATE INDEX IF NOT EXISTS idx_alerts_prediction ON alerts(risk_prediction_id);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
CREATE INDEX IF NOT EXISTS idx_tsunami_forecasts_eq ON tsunami_forecasts(earthquake_id);
CREATE INDEX IF NOT EXISTS idx_sensor_readings_station ON sensor_readings(station_id);
CREATE INDEX IF NOT EXISTS idx_sensor_readings_timestamp ON sensor_readings(timestamp DESC);

-- Relationships:
--   earthquakes (1) --- (N) risk_predictions   [one quake can be re-scored, e.g. ML model v2 rerun]
--   risk_predictions (1) --- (N) alerts          [one prediction can fan out to many SMS recipients + push + ws]

