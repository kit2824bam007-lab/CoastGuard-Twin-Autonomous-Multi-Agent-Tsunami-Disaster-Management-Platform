# Implementation & Architecture Audit Report
**Document Version:** 1.0  
**Target Submission:** IEEE Conference on Autonomous Systems and Disaster Management  
**Date:** October 2026  
**Auditor:** Research Systems & Formal Verification Team

---

## 1. Repository Inventory & Environmental Baseline

- **Repository Root:** `CoastGuard-Twin-Autonomous-Multi-Agent-Tsunami-Disaster-Management-Platform`
- **Active Git Branch:** `main`
- **Execution Environment:** Windows 11 64-bit, Python 3.12.7, Node.js v20+, FastAPI 0.115+, Scikit-learn 1.6+, Pytest 9.0+
- **Database / Infrastructure Definitions:**
  - TimescaleDB (PostgreSQL 16) in `docker-compose.yml` and `database/schema.sql`
  - Redis 7-alpine cache container
  - Eclipse Mosquitto 2.0 MQTT broker with WebSocket port 9001
  - FastAPI backend (`backend/app/main.py`)
  - React 18 + Three.js / React Three Fiber frontend (`frontend/src/`)

---

## 2. Codebase Audit: Entrypoints, Modules & Traceability

### 2.1 Backend Architecture & Application Entrypoints
- **Core Server Entrypoint:** `backend/app/main.py`
  - Lifecycle hook launches `continuous_simulation_loop()` running at 1 Hz tick rate.
  - Ticks `sim_engine.tick()`, updates `digital_twin_service`, calls `swarm_engine.tick_pso_and_pathfinding()`, classifies threat with `ml_classifier.predict()`, and broadcasts telemetry via WebSocket manager (`/ws/telemetry`).
- **Data Simulation Engine:** `backend/app/services/data_sim_engine.py`
  - Manages 50×50 static bathymetric grid.
  - Simulates seismic P/S waveforms via exponential decay functions following scenario injection (`trigger_event(magnitude, distance_km)`).
  - Simulates DART buoy water-level anomaly and shoreline state machine (`NORMAL` $\to$ `RECEDING` $\to$ `SURGING`).
- **Digital Twin Synchronization:** `backend/app/services/digital_twin.py`
  - Derives cell-by-cell inundation risk over the 50×50 grid:
    $$d_{\text{inund}} = \max(0, H_{\text{surge}} - 0.35 \cdot z(x,y) - 0.04 \cdot \text{dist}_{\text{shore}})$$
  - Maintains 300-snapshot sliding audit window.
- **Swarm Intelligence Engine:** `backend/app/services/swarm_engine.py`
  - Heterogeneous swarm roster: 3 UAVs, 3 USVs, 3 Ground rovers.
  - Dynamic Euclidean proximity mesh network ($R_{\text{comm}} = 12.0$).
  - Particle Swarm Optimization (PSO) velocity update equation:
    $$\mathbf{v}_i(t+1) = w \mathbf{v}_i(t) + c_1 r_1 (\mathbf{p}_i - \mathbf{x}_i) + c_2 r_2 (\mathbf{g}_i - \mathbf{x}_i)$$
  - Fault injection: `simulate_agent_loss(agent_id)` drops agent status to `LOST` and adjusts mesh edges.
- **Physical Wave Model:** `backend/app/services/wave_model.py`
  - Approximates deep ocean shallow-water speed ($v = \sqrt{g h} \approx 713\text{ km/h}$).
  - Abe source scaling ($H_0 = 10^{0.52 M - 3.4}$) and Green's Law coastal amplification factor ($K_s \approx 4.73$).

---

## 3. Discrepancies, Defects & Implementation Gaps Identified

### 3.1 Defect 1: Mocked Analytical Benchmarks in Legacy `benchmark_service.py`
- **Original State:** In the initial repository commit, `benchmark_service.py` calculated comparative metrics using `random.uniform()` perturbations around static offsets (e.g. `145.0 + random.uniform(-10, 15)` vs `32.0 + random.uniform(-3, 4)`).
- **Impact:** The paper's claimed improvements (80.8% latency reduction, 49.7% evacuation reduction, 61.7% search coverage increase, 34.8% path success increase) did not come from an executed simulation.
- **Action Required:** Fully integrate the discrete-event multi-trial simulation runner into the service and experimental pipeline.

### 3.2 Defect 2: Unimplemented A\* Graph Planning in Original Swarm Engine
- **Original State:** The docstring of `swarm_engine.py` claimed "A* path planning", but the method `tick_pso_and_pathfinding` only updated continuous velocity vectors ($\mathbf{v} = \mathbf{v} + \dots$) without obstacle collision avoidance, terrain slope penalties, or grid graph search.
- **Action Required:** Build and integrate an autonomous `AStarPlanner` service with 8-connected grid navigation, hazard weight penalties, and vehicle mobility constraints (UAV air, USV water, GROUND land). Verify that agents and civilians actively call A*.

### 3.3 Defect 3: Missing Dynamic Civilian Evacuation Modeling
- **Original State:** Civilian response was purely conceptual in the UI (`CivilianView.tsx`), with zero civilian agents simulated in backend physics. Evacuation times reported in Table 1 were static constants.
- **Action Required:** Implement dynamic civilian agents with spatial starting coordinates in coastal lowlands, individual walking speeds, destination routing toward safe highland shelters (+85m elevation), and drowning/trapping conditions when water depth exceeds 1.2m.

### 3.4 Defect 4: Circular Machine Learning Labeling & Class Imbalance Artifact
- **Original State:**
  - 2,400 synthetic samples were generated with labels assigned via strict if-then conditions on the exact features fed to Random Forest (`buoy_anomaly > 1.8 \implies \text{SEVERE}`).
  - Due to exponential tail sampling ($\text{Exp}(\beta=0.4)$), only 13 severe samples were generated total, resulting in exactly **2 severe test samples** in the 15% stratified test split ($N=360$).
  - One sample was classified correctly and one was misclassified as WARNING, producing exactly $1/2 = 50.0\%$ recall.
- **Action Required:**
  - Explicitly document circular synthetic labeling as a baseline rule-checking experiment.
  - Implement a physically calibrated dataset generator with continuous probabilistic scoring and sensor noise.
  - Provide noise robustness stress tests and detailed per-class metric reporting.

---

## 4. Planned Architecture Upgrades & Verification Protocol

1. **Integrated Simulation Framework (`backend/app/services/simulation_benchmark_runner.py`):**
   - Scenario parameters stored independently from algorithm logic.
   - Matched random seed pairs comparing Centralized Baseline vs Proposed Swarm across $N \ge 30$ trials.
2. **Hazard-Aware A\* Path Planner (`backend/app/services/path_planner.py`):**
   - Elevation difficulty cost, inundation depth barrier, and vehicle domain feasibility.
3. **Structured Research Output Directory Hierarchy:**
   - `results/raw/`: Trial-level CSVs and JSON traces.
   - `results/processed/`: Statistical aggregates, effect sizes, paired t-tests, Wilcoxon tests.
   - `results/figures/`: Publication-quality vector and raster charts.
   - `results/models/`: Trained Random Forest model artifacts and metadata.
   - `results/verification/`: Independent audit validation JSON report.
4. **Independent Verification Engine (`backend/app/experiments/verify_results.py`):**
   - Standalone validator recalculating every reported metric directly from raw trial logs.
5. **Comprehensive IEEE-Aligned Documentation Package:**
   - 8 specialized documentation guides covering technical architecture, methodology, provenance, experiment protocols, and claim-evidence matrices.

---

## 5. Second-Pass Audit: Critical Methodological & Algorithmic Corrections

A second-pass rigorous forensic audit identified and resolved seven critical methodological concerns:

### 5.1 Evacuation Duration & Civilian Trapping Accounting
- **Defect Identified:** Evacuation durations were previously vulnerable to conflation between transit duration ($t_{\text{complete}} - t_{\text{start}}$) and total emergency response duration ($t_{\text{complete}} - 0$). Furthermore, reporting only successful evacuees' average duration concealed the fate of trapped civilians.
- **Correction Implemented:**
  - Evacuation transit duration is calculated strictly as `completion_time - evac_start_time` for successful evacuees.
  - Four explicit event timestamps are tracked per civilian: event trigger time ($t=0$), alert dispatch time ($t_{\text{alert}}$), evacuation start time ($t_{\text{start}}$), and completion time ($t_{\text{complete}}$).
  - Evacuation completion percentage (`evacuation_completion_pct`) is reported separately from transit duration.
  - Pre-alert flood inundation checks were added: civilians awaiting late sirens in coastal lowlands who encounter $\ge 1.2$\,m floodwaters become irreversibly trapped. In the centralized baseline ($191$\,s siren latency), $80.25\%$ of civilians are trapped, leaving only $19.75\%$ escaping (those closest to shelters). Under Swarm early alerts ($72.5$\,s), $90.58\%$ evacuate safely.

### 5.2 Deterministic Random Seeds & RNG Injection
- **Defect Identified:** `CivilianAgent` initialized speeds using global `random.uniform()`, and sector allocation in `swarm_engine.py` utilized Python's process-randomized `hash(agent_id)`, introducing non-deterministic execution across Python interpreter runs.
- **Correction Implemented:**
  - Removed all calls to global `random` within simulation logic; trial-specific seeded `random.Random(seed)` instances are injected into all agents.
  - Replaced process-randomized `hash(agent_id)` with deterministic byte-sum modulo sector assignment (`sum(agent_id.encode('utf-8')) % 3`).
  - Added deterministic reproducibility regression tests in `backend/tests/test_research_benchmarks.py` confirming identical seeds generate bitwise-identical output metrics across runs.

### 5.3 Detection and Alert Timing Pipeline
- **Defect Identified:** Detection delays lacked transparent breakdown between physical sensing, consensus decision, and transmission.
- **Correction Implemented:**
  - Decomposed detection-to-alert latency into four discrete simulation pipeline timestamps:
    1. $t_{\text{obs}}$ (`observation_time_sec`): Time an agent's sensor observes anomalous wave threshold.
    2. $t_{\text{dec}}$ (`decision_time_sec`): Time multi-agent confirmation threshold is reached.
    3. $t_{\text{trans}}$ (`transmission_time_sec`): Multi-hop mesh propagation time across acoustic/RF links.
    4. $t_{\text{alert}}$ (`alert_dispatch_time_sec`): Final siren broadcast to civilian population.
  - Disclosed that communication latencies and sensor response times are modeled under simulation assumptions rather than physical in-situ hardware measurements.

### 5.4 A\* Search Correctness & Corner-Cutting Prevention
- **Defect Identified:** Diagonal movements could cut corners across adjacent impassable barrier cells. Start and goal cells were not pre-validated for traversability. Elevation cost lacked true adjacent-cell elevation difference modeling.
- **Correction Implemented:**
  - Added strict diagonal corner-cutting prevention: for any diagonal move $(dx, dy)$, traversal is forbidden if orthogonal cells $(x+dx, y)$ or $(x, y+dy)$ are impassable.
  - Added upfront start and goal traversability validation (`math.isinf()` check).
  - Formulated slope cost based strictly on adjacent-cell elevation delta: $\alpha \max(0, z(n') - z(n))$.
  - Added hazard barrier checks preventing PSO/social forces from pushing agents across impassable water barriers.

### 5.5 Benchmark Integrity & Raw Recalculation
- **Defect Identified:** Prior benchmarks lacked transparent trial preservation when re-run.
- **Correction Implemented:**
  - Archived pre-audit benchmark runs to `results/archive_v1_pre_audit/`.
  - Re-ran 30 paired Monte Carlo trials under strictly identical seeds ($M_w=7.8, D=45$\,km).
  - Recalculated all statistics, 95% confidence intervals, and hypothesis tests directly from raw per-trial CSV logs (`raw_trials_m7.8_d45.0_n30.csv`).

### 5.6 Historical Backtest Honest Reclassification
- **Defect Identified:** The 40-event evaluation was originally framed as a continuous operational historical backtest, but was actually a curated scenario study.
- **Correction Implemented:**
  - Reclassified the test in documentation and manuscript as a "Curated Landmark Case Evaluation (40 Literature Scenarios)".
  - Disclosed that the 40 cases are notable reference events from published literature rather than an uncurated continuous catalog extraction.

### 5.7 Automated Verification & Test Coverage
- **Outcome:** Comprehensive regression tests implemented in `backend/tests/test_research_benchmarks.py`.

---

## 6. Third-Pass Audit: Docker Architecture, MQTT Integration & Full-Stack Contracts

A third-pass infrastructure and service-contract audit resolved critical containerization and integration gaps:

### 6.1 Docker Compose & Environment Hardening
- **Defects Identified:** Obsolete `version: "3.9"` declaration; hardcoded PostgreSQL passwords in compose file without `.env.example`; lack of healthchecks for Redis; lack of persistent volume for Mosquitto; and database schema not mounted into `/docker-entrypoint-initdb.d/`.
- **Corrections Implemented:**
  - Removed obsolete `version` attribute for standard Compose v2 compliance.
  - Created root [`.env.example`](file:///c:/Users/hp/Downloads/tsunami/.env.example) and configured [`.gitignore`](file:///c:/Users/hp/Downloads/tsunami/.gitignore) to exclude active `.env` files.
  - Mount `./database/schema.sql:/docker-entrypoint-initdb.d/init.sql:ro` so fresh PostgreSQL containers initialize all tables automatically.
  - Added robust container healthchecks: `pg_isready -U user -d db` for postgres and `redis-cli ping` for redis.
  - Created named volume `mqttdata` mounted to `/mosquitto/data`.
  - Added backend healthcheck testing `http://localhost:8000/health`.

### 6.2 MQTT Service Integration (Eclipse Mosquitto)
- **Defect Identified:** The MQTT broker was declared in Compose, but no MQTT client or topics existed in backend code.
- **Corrections Implemented:**
  - Created [`backend/app/services/mqtt_service.py`](file:///c:/Users/hp/Downloads/tsunami/backend/app/services/mqtt_service.py) with resilient non-blocking connection to `mqtt-broker:1883`.
  - Defined explicit topic contracts: `coastguard/telemetry` (1 Hz telemetry broadcast), `coastguard/alerts` (emergency warnings), and `coastguard/commands` (simulation trigger/reset listener).
  - Wired MQTT lifecycle into FastAPI `lifespan` in [`backend/app/main.py`](file:///c:/Users/hp/Downloads/tsunami/backend/app/main.py).

### 6.3 Frontend Build-Time Addressing & WebSocket Proxying
- **Defects Identified:** Vite bakes `import.meta.env.VITE_API_BASE_URL` into bundles at build-time, so runtime compose environment variables were ignored. Frontend WebSocket in `App.tsx` hardcoded `window.location.host` which failed on static container servers.
- **Corrections Implemented:**
  - Added `ARG VITE_API_BASE_URL` and `ENV VITE_API_BASE_URL` to [`frontend/Dockerfile`](file:///c:/Users/hp/Downloads/tsunami/frontend/Dockerfile) and passed them in `docker-compose.yml`.
  - Exported `API_BASE`, `WS_BASE`, and `apiUrl(endpoint)` helper from [`frontend/src/api/client.js`](file:///c:/Users/hp/Downloads/tsunami/frontend/src/api/client.js).
  - Updated all fetch and WebSocket connections in `App.tsx` and UI components to use `apiUrl` and `WS_BASE`.

### 6.4 API Route Registration & Frontend Alignment
- **Defects Identified:** Routers `data.py`, `predict.py`, and `command.py` were not included in `app.main.py`, causing 404 errors for frontend earthquake lists and command overviews. Database sensors endpoints were missing.
- **Corrections Implemented:**
  - Registered all missing routers in `backend/app/main.py`.
  - Added `/sensors/` and `/sensors/readings/{station_id}` endpoints in `backend/app/routers/sensors.py`.
  - Added automated integration tests in [`backend/tests/test_docker_integration.py`](file:///c:/Users/hp/Downloads/tsunami/backend/tests/test_docker_integration.py).

### 6.5 Full Test Suite Pass
- **Outcome:** The automated test suite stands at **41 passed, 0 failed, 0 warnings** across all 8 test modules. Both backend and frontend Docker containers build with exit code 0.
