# Research Audit Report: CoastGuard Twin Platform
**Document Version:** 1.0  
**Target Submission:** IEEE Conference on Autonomous Systems, Multi-Agent Coordination & Disaster Technologies  
**Date of Audit:** October 2026  
**Auditor:** Senior Research Systems & Verification Team

---

## 1. Executive Summary & Purpose

This research audit conducts an exhaustive, forensic inspection of the **CoastGuard Twin** repository (`kit2824bam007-lab/CoastGuard-Twin-Autonomous-Multi-Agent-Tsunami-Disaster-Management-Platform`). The objective is to identify discrepancies between published/reported research claims and the underlying software implementation, evaluate experimental rigor, uncover methodological flaws (such as circular label synthesis and metric mocking), and establish a concrete, prioritized roadmap for IEEE conference paper readiness.

---

## 2. Architecture & Data Flow Analysis

### 2.1 The Five-Layer Pipeline

The platform is structured conceptually as a five-layer digital twin and multi-agent coordination system:

```
┌────────────────────────────────────────────────────────────────────────┐
│ Layer 1: Sensing & Data Acquisition                                    │
│   • Synthetic P/S Wave seismic stream (Richter-scaled decay)          │
│   • DART Buoy sea-level anomaly generator                             │
│   • 50x50 Coastal bathymetry & elevation matrix                       │
│   • Shoreline camera state machine (NORMAL / RECEDING / SURGING)       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ 1 Hz State Snapshot
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Layer 2: Digital Twin Synchronization                                  │
│   • Cell-by-cell inundation risk estimation over 50x50 grid            │
│   • Multi-sensor state fusion & sliding 300-snapshot audit memory     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Spatial Inundation & Threat States
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Layer 3: Swarm Intelligence Coordination                               │
│   • Heterogeneous agent swarm: 3 UAVs (Air), 3 USVs (Sea), 3 Ground    │
│   • Proximity mesh topology calculation (Euclidean comm radius = 12.0) │
│   • PSO velocity updates toward personal & neighbor best targets       │
│   • Dynamic mesh self-healing on simulated agent failure               │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Agent Positions & Telemetry
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Layer 4: Visualization & Alert Dispatch                                │
│   • 3D Command Center (React Three Fiber, OrbitControls, WebXR)        │
│   • Civilian Evacuation View (Nearest shelter vector, TTS, PWA)        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Telemetry Streaming
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Layer 5: Decision Support & Benchmarking                               │
│   • Random Forest 4-class hazard classifier                            │
│   • Comparative benchmark metrics engine (Baseline vs Proposed)        │
└────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Actual Implementation vs. Documented Claims

A line-by-line inspection of the backend services revealed significant divergence between what was documented or claimed in research summaries and what is actually implemented:

| Component / Claim | Claimed in Documentation / Paper | Actual Implementation Status in Repository |
| :--- | :--- | :--- |
| **A\* Path Planning** | "Heterogeneous swarm ... executing A\* path planning over hazard terrain" (`swarm_engine.py` docstring, README §8) | **NOT IMPLEMENTED.** `swarm_engine.py` only implements direct velocity integration (`vx, vy` clamping). No graph search, heuristic cost function, or obstacle/inundation avoidance exists. |
| **Benchmark Metrics Engine** | "Empirical benchmark evaluation comparing Centralized Baseline vs. Swarm Digital Twin across 2,400 runs" | **MOCKED / SYNTHETIC NOISE.** `benchmark_service.py` (`_generate_benchmark_comparison`) drew numbers from `random.uniform()` around fixed hardcoded constants (`145.0s`, `38.5m`, `62.4%`, `74.2%`). It did not run a simulation trial. |
| **Evacuation Time Simulation** | "49.7% reduction in evacuation time for civilian populations" | **NO CIVILIAN AGENT SIMULATION.** Civilian movement was entirely static. Evacuation time was an analytical constant in `benchmark_service.py`, not a dynamic multi-agent or agent-based evacuation model. |
| **ML Classifier Dataset** | "2,400 synthetic samples evaluating hazard severity" | **IMPLEMENTED BUT HIGHLY CIRCULAR.** `ml_classifier.py` generates 2,400 samples using synthetic exponential distributions. Ground truth labels are assigned by strict if-then rules on the exact features provided to the model. |
| **Decentralized Coordination** | "Decentralized swarm digital twin platform" | **CENTRALIZED RUNTIME.** The swarm simulation, mesh topology calculation, digital twin state, and ML classification are executed inside a single centralized FastAPI server process (`continuous_simulation_loop`). While the algorithmic logic models local ad-hoc communication, the deployment architecture is centralized. |
| **Fault-Tolerance / Failover** | "Self-healing mesh and satellite failover" | **ALGORITHMIC HEALING PARTIAL; INFRASTRUCTURE CENTRAL.** In `swarm_engine.py`, dropping an agent removes its edges and flags remaining agents to broaden search. Satellite toggle changes a boolean flag (`channel_type = 'LEO_SATELLITE'`). Redis, Postgres, and FastAPI are single points of failure. |
| **Physical Wave Model** | "Hydrodynamic tsunami modeling" | **HEURISTIC APPROXIMATION.** `wave_model.py` uses shallow water speed $v = \sqrt{g h}$, Green's Law coastal amplification $(h_{\text{deep}}/h_{\text{coast}})^{0.25}$, and Abe's empirical formula. `digital_twin.py` uses a linear depth-decay heuristic. |

---

## 3. Analysis of Existing Experimental Methodology

### 3.1 Machine Learning Hazard Classifier Audit

Located in `backend/app/services/ml_classifier.py`:
- **Model Type:** Scikit-learn `RandomForestClassifier(n_estimators=100, random_state=42)`.
- **Dataset Generation:** `_generate_synthetic_dataset(num_samples=2400)`.
- **Features (6):**
  1. `p_wave`: Primary seismic waveform amplitude ($\text{Exp}(\lambda=10.0)$).
  2. `s_wave`: Secondary seismic waveform amplitude ($\text{Exp}(\lambda=5.0)$).
  3. `buoy_anomaly`: Sea-level anomaly in meters ($\text{Exp}(\lambda=2.5)$).
  4. `shoreline_code`: Categorical integer ($0=\text{NORMAL}, 1=\text{RECEDING}, 2=\text{SURGING}$).
  5. `max_inundation_m`: $\max(0, 1.5 \times \text{buoy\_anomaly} - \mathcal{U}(0, 1))$.
  6. `distance_km`: Epicenter distance $\mathcal{U}(10.0, 200.0)$.
- **Target Assignment Logic:**
  ```python
  if buoy_anomaly > 1.8 or max_inundation > 2.5 or (s_wave > 1.5 and shoreline_code == 2):
      label = 3 # SEVERE
  elif buoy_anomaly > 0.8 or max_inundation > 1.0 or s_wave > 0.8:
      label = 2 # WARNING
  elif buoy_anomaly > 0.3 or s_wave > 0.3 or shoreline_code == 1:
      label = 1 # WATCH
  else:
      label = 0 # NO_THREAT
  ```

#### Critical Methodological Defects Uncovered:
1. **Circular Label Generation (Synthetic Data Leakage):**
   The labels are direct deterministic step functions of `buoy_anomaly`, `max_inundation`, `s_wave`, and `shoreline_code`. The Random Forest is effectively learning an explicit if-else decision tree that was written into the dataset generator. This explains the near-perfect accuracy (99.4%) and cannot be presented as proof of generalized predictive capability.
2. **Extreme Class Imbalance & The "50% SEVERE Recall" Artifact:**
   - Because `buoy_anomaly` follows $\text{Exp}(\text{scale}=0.4)$, the probability of $P(\text{buoy} > 1.8) = e^{-1.8 / 0.4} = e^{-4.5} \approx 0.011$ (1.1%).
   - In the 2,400 generated samples, only 13 samples belong to the `SEVERE` class.
   - Under the 70/15/15 stratified split, the test set has exactly **2 SEVERE samples**.
   - During evaluation, 1 sample was classified correctly as `SEVERE` and 1 sample was misclassified as `WARNING`.
   - **Result:** $1 / 2 = 50.0\%$ recall!
   - Reporting a "50% SEVERE recall" without reporting the denominator ($N=2$) creates a false illusion of statistical measurement. A single sample flip changes recall from 50% to 100% or 0%.

### 3.2 Tsunami Simulation Benchmark Audit

Located in `backend/app/services/benchmark_service.py`:
- In the existing code, `_generate_benchmark_comparison` calculates:
  - `base_detection_time = round(145.0 + random.uniform(-10.0, 15.0) + (10.0 - mag) * 5.0, 1)`
  - `swarm_detection_time = round(32.0 + random.uniform(-3.0, 4.0), 1)`
  - `base_evac_time = round(38.5 + random.uniform(-3.0, 5.0), 1)`
  - `swarm_evac_time = round(19.2 + random.uniform(-1.5, 2.0), 1)`
  - `base_coverage = round(62.4 + random.uniform(-4.0, 4.0), 1)`
  - `swarm_coverage = round(96.8 + random.uniform(-1.5, 1.5), 1)`
  - `base_path_success = round(74.2 + random.uniform(-5.0, 5.0), 1)`
  - `swarm_path_success = round(98.4 + random.uniform(-1.0, 1.0), 1)`

#### Critical Methodological Defects Uncovered:
1. **Mocked Empirical Results:**
   The reported numbers in the paper (80.8% latency reduction, 49.7% evacuation reduction, 61.7% search coverage increase, 34.8% path planning increase) were derived from random perturbations around hardcoded numbers, not from dynamic simulation runs.
2. **Missing Real Baseline Comparison:**
   There is no implemented centralized coordinator running identical simulation trials side-by-side with the multi-agent swarm.
3. **No Statistical Dispersion:**
   No multi-trial variances, confidence intervals, seed sensitivity, or scenario ablations were computed.

---

## 4. Current Reproducibility Assessment

| Dimension | Assessment | Details |
| :--- | :--- | :--- |
| **Python Test Suite** | Passed with 2 Failures | 21 tests pass; 2 live-network tests fail due to rigid type assertions on USGS/NOAA feeds. |
| **Random Seeds** | Partially Set | Seed `42` is hardcoded in ML scripts; simulation runtime relies on `random.random()` without session seed management. |
| **CLI Reproducibility** | Missing | No standalone CLI commands existed to rerun benchmarks, generate datasets, or export raw CSV/JSON logs. |
| **Docker Compose** | Functional | Container definitions exist for backend, frontend, Postgres, Redis, Mosquitto. |

---

## 5. Prioritized Implementation & Remediation Plan

To elevate this codebase to IEEE publication standards while maintaining complete research integrity:

1. **Step 1: Document Exact Historical Results Reproduction (`docs/RESULTS_REPRODUCTION.md`)**
   Forensically document how the 99.4% accuracy, 91.3% macro F1, 50% SEVERE recall, and benchmark improvement percentages were generated.
2. **Step 2: Build Real Multi-Agent Simulation & Centralized Baseline Engine**
   - Implement real A* path planning over the 50x50 bathymetry and inundation grid with hazard-weight cost heuristics.
   - Implement real civilian evacuation agents attempting to reach safe shelters (+85m elevation) while inundation spreads.
   - Implement a genuine centralized baseline (single centralized controller with telemetry polling delay and communication bottleneck) running the identical hazard scenario.
   - Implement search area coverage calculation based on agent sensor footprints over the grid.
3. **Step 3: Multi-Trial Benchmarking & Ablation Suite**
   - Provide a parameterized benchmark runner executing $N$ independently seeded trials.
   - Measure real detection latency, evacuation completion time, cell coverage %, path success %, agent loss recovery, and communication overhead.
   - Execute ablation studies comparing:
     1. Full Proposed Multi-Agent Swarm (PSO + A* + Dynamic Mesh)
     2. Swarm without PSO (Random Walk / Fixed Sector Patrol)
     3. Swarm without A* (Direct Line / Uninformed Trajectory)
     4. Swarm without Mesh Communication (Isolated Agents)
     5. Centralized Baseline (Single Dispatch Hub)
   - Export raw trial data to `results/benchmark/` and `results/ablation/` in CSV and JSON formats with mean, standard deviation, and 95% confidence intervals.
4. **Step 4: Machine Learning Rigor & Class Imbalance Resolution**
   - Retain original synthetic dataset generator for historical reproducibility.
   - Add balanced / physically consistent generation options with realistic class distributions.
   - Implement comprehensive evaluation reporting per-class precision, recall, F1, balanced accuracy, confusion matrix, and explicit sample counts.
   - Transparently document synthetic circularity and clearly position the classifier.
5. **Step 5: Code Quality & Test Suite Fixes**
   - Fix failing USGS and NOAA network tests in `test_live_network.py`.
   - Add comprehensive tests for A* pathfinding, multi-trial benchmarking, and metric calculations.
6. **Step 6: IEEE Paper Revision Guide (`docs/IEEE_PAPER_REVISION_GUIDE.md`)**
   - Map every scientific claim to code, identify overclaims, provide corrected mathematical formulations, and supply verified citations.
