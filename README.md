# CoastGuard Twin — Autonomous Multi-Agent Tsunami Disaster Management Platform

> [!IMPORTANT]
> **SIMULATION PLATFORM DISCLAIMER**: CoastGuard Twin is a research/demo-grade decision-support platform demonstrating closed-loop digital twin synchronization, swarm intelligence coordination, and metaverse 3D visualization. **This is a research/demo simulation tool, not a certified operational warning system.**

---

## Architecture Overview — 5-Layer Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│              LAYER 1 — SENSING & DATA ACQUISITION                      │
│   Seismic Waveforms (P/S) | DART Buoys | 50x50 Bathymetry | Cameras    │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ Continuous 1 Hz Feeds (MQTT / REST)
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              LAYER 2 — DIGITAL TWIN SYNCHRONIZATION                     │
│   Sensor Fusion | Inundation Risk Heuristics | Audit Snapshots         │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ Synchronized Twin State (Topic: twin)
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              LAYER 3 — SWARM INTELLIGENCE COORDINATION                   │
│   Heterogeneous Swarm (UAV/USV/Ground) | Proximity Mesh | PSO | A*       │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ Swarm Telemetry & Route Verification
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              LAYER 4 — METAVERSE VISUALIZATION & PUBLIC ALERT           │
│   Operator Command Center 3D (R3F + WebXR) ◄──► Civilian PWA Offline View│
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ Hazard State & Ground Confidence
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              LAYER 5 — DECISION SUPPORT, ML & BENCHMARKING              │
│   RandomForest Classifier | Live Confusion Matrix | Comparative Metrics│
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🌟 Key Features

1. **Layer 1 (Sensing)**: Real-time simulation of P/S wave seismic signals, DART buoy sea-level anomalies, 50x50 coastal bathymetry grid, and camera shoreline flags with event injection triggers.
2. **Layer 2 (Digital Twin)**: Multi-sensor fusion engine deriving cell-by-cell inundation risk over coastal terrain using elevation, shore distance, and wave surge heuristics.
3. **Layer 3 (Swarm Intelligence)**: Heterogeneous agent swarm (Air UAVs, Sea USVs, Land Ground Rovers) executing decentralized Particle Swarm Optimization (PSO) task allocation and dynamic proximity mesh topology with self-healing re-routing upon agent failure.
4. **Layer 4 (Metaverse 3D & Civilian View)**:
   - **Command Center 3D**: Explorable React Three Fiber scene with terrain elevation mesh, ocean water layer, live 3D agent markers, mesh edge links, inundation heatmap, and WebXR VR/AR capability button (with OrbitControls fallback).
   - **Civilian View**: Mobile-first evacuation card layout with directional compass, nearest shelter guidance (+85m elevation), plain-language action steps, and Service Worker PWA offline caching.
5. **Layer 5 (ML Classifier & Metrics)**:
   - RandomForest 4-class hazard severity classifier trained on 2,400 synthetic samples (70/15/15 train/val/test split).
   - Live $4 \times 4$ Confusion Matrix (Figure 5) and empirical metrics (Accuracy, Precision, Recall, F1).
   - Comparative Benchmarking Dashboard (Table 1 / Figure 7): Centralized Single-Node Baseline vs. Proposed Multi-Agent Swarm System.

---

## 🚀 Quick Start & Setup Instructions

### Option 1: Running with Docker Compose (Full Stack)

Ensure Docker Desktop is running on your machine:
```bash
docker-compose up --build
```
This spins up:
- **`postgres`**: TimescaleDB on port `5432`
- **`redis`**: Redis cache on port `6379`
- **`mqtt-broker`**: Eclipse Mosquitto on MQTT port `1883` & WebSockets port `9001`
- **`backend`**: FastAPI engine on `http://localhost:8000`
- **`frontend`**: React Three Fiber UI on `http://localhost:5173`

### Option 2: Running Standalone Locally

#### 1. Backend Setup:
```bash
cd backend
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### 2. Frontend Setup:
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## 🎮 Scripted "Trigger Event" Demo Walkthrough

To execute a complete end-to-end demonstration scenario:

```bash
python backend/seed_demo.py
```
Or manually click **"Trigger Scenario"** (Magnitude 7.8, Epicenter 45 km) in the UI top navbar:
1. Observe live seismic P/S waveform spike on mini-charts.
2. Watch the Layer 2 Digital Twin inundation heatmap spread over 3D coastal terrain.
3. Observe Layer 3 UAV/USV/Ground agents auto-adjust search vectors and proximity mesh topology lines.
4. Click **"Disable Agent"** on any 3D node to demonstrate PSO mesh self-healing and task redistribution.
5. Switch to **Civilian Evacuation View** to inspect `SEVERE` alert level, directional shelter compass, and offline PWA service worker status.
6. Open **ML & Benchmark Metrics** tab to review model accuracy/F1 score, $4 \times 4$ confusion matrix, and Centralized Baseline vs. Swarm performance bar charts.

---

## 🔬 Research Reproducibility & Benchmark Suite (IEEE Verification)

CoastGuard Twin includes an automated, empirically reproducible experiment suite to verify research claims, train ML models, run multi-trial Monte Carlo simulations, and export machine-readable CSV/JSON outputs.

### 1. Reproduce Historical Paper Figures
Re-runs the exact historical ML classifier and benchmark calculations to verify original paper metrics:
```bash
python backend/app/experiments/reproduce_paper.py
```
*Outputs: `results/reproduction/reproduction_summary.json`*

### 2. Machine Learning Training & Noise Stress Testing
Train and evaluate the Random Forest Hazard Classifier with full metadata logging:
```bash
# Train on historical 2,400 synthetic samples or calibrated physics mode:
python backend/app/experiments/train_ml.py --mode historical --samples 2400 --seed 42
python backend/app/experiments/train_ml.py --mode calibrated --samples 2400 --seed 42

# Evaluate test set with noise perturbation stress tests:
python backend/app/experiments/evaluate_ml.py --mode historical
python backend/app/experiments/evaluate_ml.py --mode calibrated
```
*Outputs: `results/classifier/` (model `.joblib`, evaluation summary `.json`, per-class `.csv`)*

### 3. Multi-Trial Simulation Benchmark (Centralized vs. Swarm)
Executes $N=30$ independently seeded discrete-event simulation trials with dynamic civilian evacuation over the 50x50 coastal grid:
```bash
python backend/app/experiments/run_benchmark.py --trials 30 --magnitude 7.8 --distance_km 45.0 --seed 100
```
*Outputs: `results/benchmark/` (`raw_trials_*.csv`, `summary_metrics_*.csv`, `benchmark_full_report_*.json` with Mean, Std, and 95% Confidence Intervals)*

### 4. Component Ablation Studies
Evaluates the individual contributions of PSO task allocation, A* path planning, Proximity Mesh communication, and Centralized dispatch across 5 variants:
```bash
python backend/app/experiments/run_ablation.py --trials 15 --magnitude 7.8 --distance_km 45.0 --seed 200
```
*Outputs: `results/ablation/` (`ablation_summary_*.csv`, `ablation_report_*.json`)*

### 5. Automated Research Test Suite
Execute the test suite validating A* obstacle avoidance, simulation mechanics, and metric calculations:
```bash
# Windows PowerShell:
$env:PYTHONPATH="backend"; python -m pytest backend/tests

# Linux/macOS:
PYTHONPATH=backend pytest backend/tests
```

### 📚 Research Documentation & Audit Reports
- [docs/RESEARCH_AUDIT.md](docs/RESEARCH_AUDIT.md) — Comprehensive architecture and methodology audit.
- [docs/RESULTS_REPRODUCTION.md](docs/RESULTS_REPRODUCTION.md) — Forensic reproduction of all historical figures.
- [docs/IEEE_PAPER_REVISION_GUIDE.md](docs/IEEE_PAPER_REVISION_GUIDE.md) — Claim-to-evidence matrix, mathematical notation, and IEEE reviewer alignment.
- [docs/backtest_report.md](docs/backtest_report.md) — Historical model validation across 40 landmark earthquakes.
- [docs/literature-review-and-comparison.md](docs/literature-review-and-comparison.md) — Comparative literature review against 7 IEEE papers.

## 📡 API Reference

- `GET /health` — Liveness & status probe
- `GET /api/sensors/snapshot` — Latest sensor snapshot & waveform history
- `GET /api/sensors/bathymetry` — 50x50 coastal bathymetry grid array
- `POST /api/sensors/trigger-event` — Inject simulated earthquake scenario (`{ magnitude, distance_km }`)
- `POST /api/sensors/reset` — Return simulation to nominal state
- `GET /api/twin/state` — Fused digital twin state & inundation risk grid
- `GET /api/twin/history` — Time-series snapshot audit history
- `GET /api/swarm/agents` — Swarm agent roster state
- `GET /api/swarm/topology` — Dynamic mesh graph nodes and edges
- `POST /api/swarm/deploy` — Deploy new UAV/USV/Ground agent
- `POST /api/swarm/simulate-loss` — Inject failure/loss for specific agent
- `GET /api/alerts/severity` — 4-class ML hazard classification & instructions
- `GET /api/metrics/classifier` — ML model evaluation metrics & confusion matrix
- `GET /api/metrics/benchmark` — Centralized vs. Swarm performance benchmarks
- `WS /ws/telemetry` — Real-time 1 Hz WebSocket telemetry stream
