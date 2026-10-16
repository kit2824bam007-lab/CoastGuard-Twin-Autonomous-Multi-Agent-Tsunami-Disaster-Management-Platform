# CoastGuard Twin — Docker & Infrastructure Deployment Guide
**Document Version:** 1.0  
**Target Environment:** Local Development & Containerized Testing  
**Auditor / Engineer:** Senior DevOps & Research Systems Engineer  

---

## 1. Overview & Service Architecture

CoastGuard Twin uses a multi-container Docker Compose architecture comprising five dedicated services:

```mermaid
graph TD
    Client["Browser / Host (Port 5173 / 8000)"]
    Frontend["Frontend Container (node:20-alpine / serve)<br>Port 5173"]
    Backend["Backend Container (python:3.12-slim / FastAPI)<br>Port 8000"]
    Postgres["TimescaleDB / Postgres 16<br>Port 5432"]
    Redis["Redis 7-alpine<br>Port 6379"]
    Mosquitto["Eclipse Mosquitto 2.0 MQTT<br>Ports 1883 (TCP) & 9001 (WS)"]

    Client -->|HTTP / SPA| Frontend
    Client -->|REST & /ws/telemetry| Backend
    Frontend -->|apiUrl & WS_BASE| Backend
    Backend -->|asyncpg pool| Postgres
    Backend -->|aioredis Pub/Sub| Redis
    Backend -->|paho-mqtt pub/sub| Mosquitto
```

### Container Roster & Port Bindings

| Service | Image | Internal Port | Host Port | Purpose | Healthcheck |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **`postgres`** | `timescale/timescaledb:latest-pg16` | `5432` | `5432` | Relational & time-series storage | `pg_isready -U user -d db` |
| **`redis`** | `redis:7-alpine` | `6379` | `6379` | Telemetry Pub/Sub cache | `redis-cli ping` |
| **`mqtt-broker`** | `eclipse-mosquitto:2.0` | `1883`, `9001` | `1883`, `9001` | IoT sensor telemetry & command broker | Socket / Process check |
| **`backend`** | Custom (`./backend/Dockerfile`) | `8000` | `8000` | FastAPI 1 Hz simulation & API layer | `urllib.request /health` |
| **`frontend`** | Custom (`./frontend/Dockerfile`) | `5173` | `5173` | React 18 + Three.js Metaverse UI | Web server process |

---

## 2. Environment Variables & Secret Management

All service configuration is consolidated in `.env` at the repository root. A template is provided in [`.env.example`](file:///c:/Users/hp/Downloads/tsunami/.env.example).

> [!IMPORTANT]
> Never commit actual passwords or `.env` files to source control. [`.gitignore`](file:///c:/Users/hp/Downloads/tsunami/.gitignore) is configured to ignore all `.env` files except `.env.example`.

### Key Environment Variables

```bash
# --- PostgreSQL & TimescaleDB ---
POSTGRES_USER=tsunami_user
POSTGRES_PASSWORD=tsunami_secure_dev_password
POSTGRES_DB=tsunami_db
POSTGRES_PORT=5432
DATABASE_URL=postgresql+asyncpg://tsunami_user:tsunami_secure_dev_password@postgres:5432/tsunami_db

# --- Redis Cache & Pub/Sub ---
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://redis:6379/0

# --- Eclipse Mosquitto MQTT ---
MQTT_BROKER_HOST=mqtt-broker
MQTT_BROKER_PORT=1883
MQTT_WS_PORT=9001

# --- Backend Application ---
BACKEND_PORT=8000
API_KEY=change_me_to_a_long_random_dev_string
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# --- Frontend Application ---
FRONTEND_PORT=5173
VITE_API_BASE_URL=http://localhost:8000
```

---

## 3. Database Initialization & Persistence

1. **Auto-Mount Schema:** The initialization script [`database/schema.sql`](file:///c:/Users/hp/Downloads/tsunami/database/schema.sql) is mounted directly to `/docker-entrypoint-initdb.d/init.sql:ro`. When the database container initializes a fresh volume, all tables are created automatically before the database reports healthy.
2. **Backend Lifespan Schema Hook:** The backend entrypoint [`backend/app/main.py`](file:///c:/Users/hp/Downloads/tsunami/backend/app/main.py) also invokes `await init_db()` inside its asynchronous lifespan context manager. If running against an existing database, it verifies schema tables; if running offline without a database container, it logs a non-fatal warning and continues in in-memory simulation mode.
3. **Named Volume:** Data persistence is maintained in named Docker volume `pgdata`.

---

## 4. MQTT Broker Integration & Topics

Mosquitto configuration is mounted from [`mosquitto.conf`](file:///c:/Users/hp/Downloads/tsunami/mosquitto.conf):
- **Port 1883:** Native TCP MQTT protocol for backend publisher/subscriber and IoT nodes.
- **Port 9001:** WebSockets MQTT protocol for direct browser sensor feeds.
- **Persistence:** Mounted to named Docker volume `mqttdata:/mosquitto/data`.

### Topic Architecture

| Topic | Publisher | Subscribers | Payload Contract |
| :--- | :--- | :--- | :--- |
| **`coastguard/telemetry`** | Backend `MqttService` | Coastal IoT Monitors, UI | 1 Hz fused digital twin + swarm state snapshot |
| **`coastguard/alerts`** | Backend `MqttService` | Sirens, Authority Gateways | Emergency evacuation alert with risk level |
| **`coastguard/commands`** | Operator / External Script | Backend `MqttService` | `TRIGGER_EVENT` or `RESET` simulation action |

---

## 5. Frontend Build-Time & Runtime Addressing

In Vite, environment variables prefixed with `VITE_` are baked into client-side JavaScript bundles at **build time**.
1. **Dockerfile Build Argument:** [`frontend/Dockerfile`](file:///c:/Users/hp/Downloads/tsunami/frontend/Dockerfile) accepts `ARG VITE_API_BASE_URL` and passes it to `npm run build`.
2. **Docker Compose Forwarding:** [`docker-compose.yml`](file:///c:/Users/hp/Downloads/tsunami/docker-compose.yml) passes `args: { VITE_API_BASE_URL: "${VITE_API_BASE_URL:-http://localhost:8000}" }`.
3. **Client Helper (`apiUrl` & `WS_BASE`):** [`frontend/src/api/client.js`](file:///c:/Users/hp/Downloads/tsunami/frontend/src/api/client.js) exports `apiUrl(path)` and `WS_BASE`, ensuring that both REST requests and WebSocket connections (`/ws/telemetry`) connect directly to the active backend instance.

---

## 6. How to Start and Verify Services

### Step 1: Copy Environment Template
```bash
cp .env.example .env
```

### Step 2: Build Images
```bash
docker compose build
```

### Step 3: Launch Services in Background
```bash
docker compose up -d
```

### Step 4: Verify Container Health
```bash
docker compose ps
```

Expected output:
```
NAME                    IMAGE                             STATUS                    PORTS
coastguard-backend      coastguard-backend                Up (healthy)              0.0.0.0:8000->8000/tcp
coastguard-frontend     coastguard-frontend               Up                        0.0.0.0:5173->5173/tcp
coastguard-mqtt         eclipse-mosquitto:2.0             Up                        0.0.0.0:1883->1883/tcp, 0.0.0.0:9001->9001/tcp
coastguard-redis        redis:7-alpine                    Up (healthy)              0.0.0.0:6379->6379/tcp
coastguard-timescaledb  timescale/timescaledb:latest-pg16 Up (healthy)              0.0.0.0:5432->5432/tcp
```

### Step 5: Test Endpoints
```bash
# Backend health:
curl http://localhost:8000/health

# Run end-to-end seed demo:
python backend/seed_demo.py
```

### Step 6: Graceful Shutdown
```bash
docker compose down
```
*(To remove persistent volumes, append `-v`)*
