# Research Limitations, Algorithmic Trade-Offs & Threats to Validity
**Document Version:** 1.0  
**Project:** CoastGuard Twin  
**Auditor / Reviewer:** Senior Research Systems & Verification Team  

---

## 1. Investigation of Unexpected Algorithmic Results: V2 (No-PSO) vs V1 (Full Swarm)

In our 5-variant ablation study ($N=15$ trials per variant), an apparent paradox was observed:
- **V1 (Full Swarm with PSO):** Detection latency $74.18 \pm 11.3$\,s, Evacuation Completion $85.8 \pm 10.9\%$, Spatial Coverage $41.29 \pm 4.45\%$.
- **V2 (Swarm without PSO — Fixed Periodic Patrol):** Detection latency $59.51 \pm 0.24$\,s, Evacuation Completion $99.5 \pm 1.0\%$, Spatial Coverage $36.80 \pm 1.20\%$.

### Root Cause Analysis & Scientific Trade-Off
A forensic code audit of [`backend/app/services/simulation_benchmark_runner.py`](file:///c:/Users/hp/Downloads/tsunami/backend/app/services/simulation_benchmark_runner.py#L366-L373) established that this is a **valid algorithmic trade-off**, not an implementation bug:
1. **Initial Deployment Bias:** Initial agent positions (`USV-201` at $x=8.0, y=15.0$ and `UAV-101` at $x=12.0, y=10.0$) are pre-stationed directly in the offshore epicentral corridor.
2. **Stationary Choke-Point Monitoring (V2):** Without PSO velocity exploration, agents execute fixed harmonic patrol loops around their initial locations ($\Delta x \propto \cos(0.1 t)$). Because they remain hovering directly over the wave's path of approach, they register wave anomalies rapidly ($59.5$\,s). The resulting 15-second earlier siren gives coastal lowlanders extra time to evacuate before the flood crests.
3. **Dynamic Regional Dispersion (V1):** When PSO velocity updates are enabled, agents dynamically disperse across the regional grid ($x \in [4, 45]$) to maximize regional coastal coverage ($41.3\%$ vs $36.8\%$). When dispersing, agents may be moving outward toward peripheral coastal sectors at the moment of rupture, introducing a slight delay before intersecting the wavefront.
4. **Conclusion:** Fixed stationary sensor placement provides low latency for known epicentral origins, whereas dynamic PSO coverage is superior for regional perimeter surveillance where disaster origins are uncertain.

---

## 2. Single Points of Failure & Decentralization Boundaries

While the swarm movement algorithm and peer mesh proximity equations ($R_{\text{comm}} = 12.0$) are decentralized, the overall software prototype relies on centralized infrastructure:
1. **FastAPI Application Gateway:** Centralized server hosting `/ws/telemetry` and REST endpoints.
2. **Redis Pub/Sub:** Acts as a centralized message broker for distributed alert routing. If Redis halts, fallback to in-memory broadcast occurs, but cross-instance communication is lost.
3. **Eclipse Mosquitto MQTT Broker:** Operates as a single message broker for IoT telemetry.
4. **Architectural Classification:** The platform must be honestly described as a **"Partially Decentralized Swarm with a Centralized Synchronization and Telemetry Gateway"**, not a fully peer-to-peer decentralized system.

---

## 3. Simulation Assumptions vs. Physical Real-World Sensor Physics

The platform is an academic discrete-event simulation prototype. Several physical domains are modeled using documented assumptions rather than in-situ hardware measurements:
- **Acoustic & RF Communication:** Packet delays are modeled via discrete hops rather than underwater sound-speed profiles, multipath fading, or RF interference.
- **DART Buoys:** Sea level anomalies are modeled via Abe source scaling and sinusoidal swell approximations rather than full Navier-Stokes hydrodynamic PDE solutions.
- **Civilian Movement:** Civilian agents navigate an 8-connected grid toward highland shelters (+85m elevation) with walking speeds uniformly sampled between $0.8$ and $1.4$\,m/s, and become trapped if water depth reaches $\ge 1.2$\,m. Real psychological panic and road network congestion are not modeled.

---

## 4. Machine Learning Dataset Provenance & Sample Sparsity

1. **Synthetic Rule-Based Labeling:** The historical 2,400-sample dataset was generated synthetically using feature threshold rules (e.g., $buoy > 1.8\text{m} \implies \text{SEVERE}$). Evaluating a Random Forest model on rule-generated data verifies model convergence to the rule set (99.4% accuracy), but does not prove real-world tsunami detection accuracy.
2. **Minority Class Sparsity (50.0% SEVERE Recall):** In the 15% stratified test split ($N=360$), the SEVERE class contains exactly **$N=2$ test samples** due to exponential tail sampling. With 1 true positive and 1 false negative, the reported 50.0% recall reflects sample sparsity rather than a stable statistical performance estimate.
3. **Calibrated Mitigation:** A calibrated continuous probabilistic dataset generator with simulated sensor noise was implemented in [`backend/app/experiments/train_ml.py`](file:///c:/Users/hp/Downloads/tsunami/backend/app/experiments/train_ml.py) to provide noise robustness benchmarks ($89.2\%$ accuracy under $20\%$ Gaussian noise).

---

## 5. Curated Literature Cases vs. Continuous Catalog Backtesting

The 40-case historical study in [`backend/app/services/backtesting.py`](file:///c:/Users/hp/Downloads/tsunami/backend/app/services/backtesting.py) evaluates 40 landmark seismic scenarios compiled from published disaster management literature.
- **Classification:** It is a **Curated Landmark Case Evaluation (40 Literature Scenarios)**, not an uncurated continuous backtest against the global USGS/NOAA database.
- **Performance:** On these 40 benchmark events, the rule-based risk model achieves 95.0% accuracy and 100.0% sensitivity.

---

## 6. Operational Readiness Disclaimer

> [!CAUTION]
> **Academic Research Prototype Disclaimer:**  
> CoastGuard Twin is designed and tested strictly as an academic research prototype and simulation benchmark testbed. It is **NOT certified for operational emergency deployment** and must never be used as a standalone life-safety alert system without integration into certified national meteorological and civil defense agencies.
