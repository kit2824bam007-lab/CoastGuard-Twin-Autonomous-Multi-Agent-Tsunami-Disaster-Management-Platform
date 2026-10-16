# Technical Architecture Specification: CoastGuard Twin
**Document Version:** 1.0  
**Target Submission:** IEEE Conference on Autonomous Systems and Disaster Management  
**System Classification:** Partially Decentralized Multi-Agent Digital Twin Simulation Platform  

---

## 1. Architectural Blueprint & Layer Decoupling

CoastGuard Twin coordinates heterogeneous autonomous vehicles (UAVs, USVs, Ground rovers) and synchronizes physical-virtual states across five operational layers:

```
┌────────────────────────────────────────────────────────────────────────┐
│ Layer 1: Sensing & Data Simulation (1 Hz Telemetry Stream)             │
│   • Synthetic P/S Waveform generators (Richter-scaled decay envelopes)  │
│   • DART Buoy sea-level anomaly wave packet engine                    │
│   • 50x50 Coastal bathymetry & elevation matrix                       │
│   • Coastal camera shoreline state machine (NORMAL / RECEDING / SURGE) │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Continuous 1 Hz Snapshot
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Layer 2: Digital Twin Synchronization & State Fusion                   │
│   • Cell-by-cell inundation risk calculation over 50x50 grid           │
│   • Elevation, shore distance, and surge height heuristics            │
│   • Sliding 300-snapshot audit memory ledger                          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Spatial Risk Grid & Summary
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Layer 3: Swarm Intelligence & Autonomous Path Planning                 │
│   • Heterogeneous Swarm Roster: 3 UAVs (Air), 3 USVs (Sea), 3 Ground   │
│   • Dynamic Euclidean proximity mesh network (R_comm = 12.0 grid units)│
│   • Decentralized Particle Swarm Optimization (PSO) task allocation    │
│   • Hazard-weighted 8-connected A* graph path planning                 │
│   • Dynamic self-healing mesh topology on agent loss injection         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Swarm Telemetry & Evac Waypoints
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Layer 4: Visualization & Alert Dispatch                                │
│   • 3D Command Center (React Three Fiber, OrbitControls, WebXR)        │
│   • Civilian Evacuation View (Compass guidance, TTS, PWA offline)      │
│   • OASIS Common Alerting Protocol (CAP v1.2) JSON serialization       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Threat Telemetry
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Layer 5: Decision Support & Benchmark Evaluation                       │
│   • Random Forest multi-class hazard classifier                        │
│   • Multi-trial discrete-event Monte Carlo simulation engine (N=30)   │
│   • Baseline vs. Proposed Swarm statistical evaluation (p < 0.001)    │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Specifications & Interfaces

### 2.1 Layer 1: Sensing & Data Simulation (`backend/app/services/data_sim_engine.py`)
- **Grid Resolution:** $50 \times 50$ cells ($x \in [0, 49], y \in [0, 49]$).
  - $x=0$: Deep ocean ($-200.0\text{m}$).
  - $x=20$: Coastal shoreline ($0.0\text{m}$).
  - $x=49$: Highland interior ($+120.0\text{m}$).
- **Wave Arrival & Seismic Shock:**
  - P-wave velocity: $v_p = 6.0\text{ km/s}$
  - S-wave velocity: $v_s = 3.5\text{ km/s}$
  - Peak seismic amplitude: $A_{\text{peak}} = \frac{10^{M_w - 6.0}}{\sqrt{D_{\text{km}}}}$

### 2.2 Layer 2: Digital Twin Synchronization (`backend/app/services/digital_twin.py`)
- **Cell Inundation Depth Model:**
  $$d_{\text{inund}}(x, y) = \max\Big(0, H_{\text{surge}} \cdot M_{\text{shore}} - 0.35 \cdot z(x,y) - 0.04 \cdot \max(0, x - x_{\text{coast}}(y))\Big)$$
  Where $M_{\text{shore}} \in \{1.0, 1.2, 1.5\}$ corresponds to shoreline camera states `NORMAL`, `RECEDING`, and `SURGING`.

### 2.3 Layer 3: Swarm Coordination & Path Planning (`backend/app/services/swarm_engine.py`)
- **Proximity Mesh Topology:**
  Edge exists between active agents $i$ and $j$ if:
  $$\|\mathbf{x}_i - \mathbf{x}_j\|_2 \le R_{\text{comm}} = 12.0\text{ units}$$
  Signal strength is modeled as:
  $$S_{ij} = \max\left(0.1, 1.0 - \frac{\|\mathbf{x}_i - \mathbf{x}_j\|_2}{R_{\text{comm}}}\right)$$
- **A\* Path Planning (`backend/app/services/path_planner.py`):**
  Calculates minimum-cost collision-free trajectories avoiding flooded cells ($d_{\text{inund}} \ge 1.5\text{m}$) and steep terrain slopes.

---

## 3. Decentralization Reality & Single Points of Failure

| Architectural Tier | Claimed Logical Abstraction | Actual Physical Runtime Implementation | Single Point of Failure (SPOF)? |
| :--- | :--- | :--- | :---: |
| **Agent Movement & Task Allocation** | Decentralized peer-to-peer PSO with local neighbor consensus | Simulated as concurrent agent objects within single Python process | Yes (Process crash halts all agents) |
| **Proximity Mesh Communication** | Ad-hoc wireless mesh network ($R_{\text{comm}} = 12.0$) | In-memory adjacency matrix evaluated each tick | Yes (Evaluated on centralized backend) |
| **State Synchronization** | Distributed digital twin synchronization | Centralized FastAPI service + TimescaleDB + Redis cache | **YES (SPOF)** |
| **Alert Dispatch** | Multi-channel broadcast (WebSocket, SMS, FCM) | Single Mosquitto MQTT broker & WebSocket manager | **YES (SPOF)** |

**Defensible IEEE Conclusion:** The system is an algorithmic emulation of decentralized multi-agent coordination deployed over a centralized cloud/edge container architecture. It must not be claimed as physically fault-tolerant against backend hardware failure.
