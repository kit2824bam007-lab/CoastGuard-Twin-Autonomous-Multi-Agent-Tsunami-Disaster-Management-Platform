# Limitations & Threats to Validity: CoastGuard Twin
**Document Version:** 1.0  
**Target IEEE Submission:** IEEE Conference on Autonomous Systems and Disaster Management  

---

## 1. Threats to Internal Validity

1. **Circular Synthetic Labeling in Machine Learning:**
   The original Random Forest classifier is trained on 2,400 synthetic samples where ground truth hazard labels (`NO_THREAT`, `WATCH`, `WARNING`, `SEVERE`) were assigned via deterministic threshold step functions on the exact input features (`buoy_anomaly`, `max_inundation`, `s_wave`). While this establishes that the Random Forest correctly memorizes the threshold partition rules (99.4% accuracy), it cannot be cited as proof of generalized predictive capability against unknown real-world tsunamis.
2. **Extreme Class Imbalance in Minority Tail:**
   In the 2,400 historical synthetic samples, exponential tail distribution produced only 13 total `SEVERE` cases, leading to exactly $N=2$ test samples. A single misclassified instance resulted in an apparent 50.0% recall rate. While mathematically accurate, this metric has high variance due to small sample support.
3. **Analytical & Heuristic Wave Physics:**
   Wave propagation over the 50×50 grid uses Abe's source scaling and linear shallow-water phase velocity approximations ($v = \sqrt{gh}$) coupled with empirical elevation decay. The platform does not execute 2D nonlinear shallow-water Navier-Stokes hydrodynamic solvers (such as TUNAMI-F1, GeoClaw, or Delft3D-FLOW). Runup estimates are heuristic approximations, not hydrodynamic ground truth.

---

## 2. Threats to External Validity

1. **Synthetic Grid Topography vs. Real Coastal Geometries:**
   The $50 \times 50$ grid models a stylized coastline with sinusoidal curvature and linear inland elevation. Real coastal topographies feature intricate bathymetry, estuaries, sea walls, urban road networks, and harbor resonance effects not captured in the 50×50 simulation.
2. **Civilian Evacuation Behavioral Assumptions:**
   Civilian agents in the simulation behave as rational point particles moving at constant velocity toward the nearest safe shelter. Real human evacuation involves panic delays, family regrouping, vehicular traffic congestion, blocked infrastructure, and non-compliance with evacuation orders. Simulated evacuation times and 100% survival rates must not be claimed as predictions of real human disaster mortality.
3. **Absence of Real-World Field Hardware Deployment:**
   No physical UAVs, USVs, or ground rovers were deployed in maritime environments. Environmental disturbances such as ocean currents, gale-force winds, saltwater battery degradation, and GPS multipath errors are modeled analytically rather than observed empirically.

---

## 3. Threats to Construct Validity & Decentralization Reality

1. **Algorithmic vs. Architectural Decentralization:**
   While the coordination algorithm models decentralized PSO and ad-hoc wireless mesh communication ($R_{\text{comm}} = 12.0$), the entire simulation executes inside a single Python backend process. The backend server, Redis instance, and Mosquitto MQTT broker constitute centralized single points of failure.
2. **Radio Frequency (RF) Mesh Emulation:**
   Inter-agent communication uses Euclidean distance thresholding. Real marine ad-hoc wireless communication suffers from sea-surface multipath reflection, wave shadowing, packet collisions, atmospheric humidity attenuation, and bandwidth degradation not fully modeled in simple distance-cutoff graphs.

---

## 4. Operational Safety Disclaimer

> **MANDATORY RESEARCH DISCLAIMER:** CoastGuard Twin is a research-grade decision-support and multi-agent coordination simulation platform. It is **not** certified, validated, or authorized for real-world operational tsunami warnings or public safety dispatch. Real emergency warnings must rely exclusively on authorized government monitoring agencies (e.g., NOAA PTWC, INCOIS, JMA).
