# Literature Review & Comparative Analysis
## AI-Powered Tsunami Early Warning and Disaster Response System

This document reviews seven representative IEEE (and IEEE-adjacent) publications on
tsunami/earthquake early warning systems, extracts the mathematical approach each one
takes, and places this project's rule-based risk engine in context against them —
honestly, including where this project is *weaker* than the published research.

---

## 1. Reference Papers (IEEE citation format)

**[1]** D. H. F. Pradana, E. A. Wiguna, R. Amien, A. N. Saputri, M. Wibowo, and
W. Hendriyono, "Development of Real-Time Tsunami Early Warning System Dashboard
Based on Tunami-F1 and Machine Learning in Sunda Arc, Indonesia," in *Proc. 2022
IEEE Ocean Engineering Technology and Innovation Conf. (Management and Conservation
for Sustainable and Resilient Marine and Coastal Resources)*, 2022.

**[2]** C. M. Cherian, N. Jayaraj, and S. G. Vaidyanathan, "Artificially Intelligent
Tsunami Early Warning System," in *Proc. 2010 12th Int. Conf. Computer Modelling and
Simulation (UKSIM)*, 2010, pp. 39–44, doi: 10.1109/UKSIM.2010.16.

**[3]** D. Y. Liliana and D. Priharsari, "Tsunami Early Warning Detection using
Bayesian Classifier," in *Proc. 2019 2nd Int. Conf. Computer and Informatics
Engineering (IC2IE)*, 2019, pp. 44–48, doi: 10.1109/IC2IE47452.2019.8940823.

**[4]** "Tsunami Early Warning System Architecture Based on Automation
Technologies," *IEEE Conference Publication*, IEEE Xplore Document No. 6917785.
(Full author list not resolvable from public IEEE Xplore metadata at the time of
writing — cited by document ID; verify authorship directly on IEEE Xplore before
using in a formal submission.)

**[5]** "Tsunami Early Warning and Validation System Based on Sea Water Level
Changes Using Automatic Water Level," *IEEE Conference Publication*, IEEE Xplore
Document No. 10730201. (Author list likewise not resolvable from public metadata —
verify on IEEE Xplore before formal citation.)

**[6]** "Deep Learning Models for Tsunami Forecasting," *IEEE Conference
Publication*, IEEE Xplore Document No. 10932932, 2025. (Hybrid Delft3D-FLOW +
CNN/LSTM model; author list not resolvable from public metadata.)

**[7]** [Author names redacted per query privacy], "Forecasting the Unseen:
Enhancing Tsunami Occurrence Predictions with Machine-Learning-Driven Analytics,"
*Sci*, vol. 14, no. 5, p. 175, 2025, doi: 10.3390/sci14050175. (MDPI — not IEEE, but
included because it is the closest published match to this project's rule-based/
tabular-classifier approach; Random Forest + Logistic Regression on a 1995–2023
Kaggle earthquake/tsunami dataset.)

> **Note on citation integrity:** where I could not verify a paper's full author
> list from public search snippets, I left the author field out rather than
> inventing names. Papers [4]–[6] should be pulled directly from IEEE Xplore for
> the complete, verified citation before use in an academic report.

---

## 2. What each paper actually does, mathematically

| # | Core mathematical approach |
|---|---|
| [1] | Two-track pipeline: (a) **shallow-water wave-propagation PDEs** solved numerically by the open-source TUNAMI-F1 model (linear long-wave equations over bathymetry grids) to generate a scenario database; (b) a **trained ML model** (queried against that pre-computed database) that returns wave height/arrival-time estimates in seconds instead of the minutes the PDE solver needs. |
| [2] | Rule/expert-system style AI reasoning over seismic parameters (magnitude, depth, location) to classify tsunami potential — conceptually the closest published analogue to this project's `RuleBasedRiskModel`, but from 2010, pre-dating modern ML tooling. |
| [3] | **Naive Bayes classifier**: P(tsunami \| features) ∝ P(features \| tsunami)·P(tsunami), trained on Indonesia's InaTEWS historical event data, producing a probabilistic (not merely thresholded) tsunami-potential score. |
| [4] | No predictive math — a **systems/architecture comparison** mapping industrial automation-technology components (SCADA-like patterns) onto TEWS functional blocks. Closest published analogue to this project's *software architecture* (not its risk model). |
| [5] | **Anomaly/threshold detection** on real-time IoT sea-level sensor time series — a statistical deviation from baseline tide curve triggers a local alert (LED/siren/speaker), no offshore earthquake correlation. |
| [6] | **CNN + LSTM** deep sequence models trained to reproduce Delft3D-FLOW hydrodynamic simulation outputs (wave amplitude over time), optimized via MSE loss on single-step and multi-step forecasting horizons. |
| [7] | **Random Forest** and **Logistic Regression** binary classifiers (tsunami / no tsunami) trained on six seismic features (magnitude, depth, coordinates, aftershock pattern, seismic moment, source mechanism) from a labeled 1995–2023 historical dataset. |

### This project's math, for direct comparison

The deployed `RuleBasedRiskModel` (see `backend/app/services/risk_model.py`) computes:

```
R = clip( f_M(m) + f_D(d) + w_O·𝟙[offshore] + w_Z·𝟙[in high-risk zone]
          + w_U·𝟙[USGS tsunami flag] + w_N·𝟙[active NOAA bulletin],  0, 1 )

f_M(m) = 0.45 if m≥8.0 ; 0.30 if 7.0≤m<8.0 ; 0.15 if 6.5≤m<7.0 ; 0 otherwise
f_D(d) = 0.20 if d≤30km ; 0.10 if 30<d≤70km ; 0 otherwise
w_O = 0.15,  w_Z = 0.10,  w_U = 0.20,  w_N = 0.20

risk_level = SEVERE if R≥0.75; HIGH if R≥0.50; MODERATE if R≥0.25; else LOW
```

This is a **hand-weighted additive scoring function** — closest in spirit to [2]
(2010, expert-rule AI) and structurally similar to a linear model with fixed
(not learned) coefficients. It is explicitly *not* a trained classifier: the
weights are engineering judgment, not fit to labeled historical data the way
[3] and [7] fit theirs, and it does not solve or approximate the physical wave
equations the way [1] and [6] do.

---

## 3. Comparison table

| Dimension | [1] Tunami-F1+ML | [2] Cherian et al. | [3] Bayesian | [4] Automation Arch. | [5] IoT Water Level | [6] CNN-LSTM+Delft3D | [7] RF/LogReg | **This project** |
|---|---|---|---|---|---|---|---|---|
| Risk model type | Hybrid: numerical PDE + ML lookup | Rule-based AI (2010) | Naive Bayes (probabilistic) | None (architecture only) | Threshold/anomaly | Deep learning (CNN+LSTM) | Trained classifiers (RF, LogReg) | **Rule-based weighted score (this)**, ML-ready fallback slot |
| Trained on real historical data | Yes (simulation database) | Not specified | Yes (InaTEWS) | N/A | N/A (live sensor only) | Yes (Delft3D-generated) | Yes (Kaggle 1995–2023) | **No** — weights are engineered, not fit |
| Real-time live public data feed | Earthquake trigger only | Not specified | Historical batch | N/A | Live IoT sensor | Simulation-driven | Historical batch | **Yes — polls live USGS + NOAA every 60s** |
| End-to-end deployable software system | Dashboard prototype | Not specified | Not specified | Conceptual proposal | Field-tested hardware+firmware | Forecasting model only | Notebook-style ML pipeline | **Yes — full FastAPI+React+Postgres stack, containerized** |
| Multi-channel alert dispatch (SMS/push/live dashboard) | Dashboard only | Not specified | Not specified | Not specified | Local siren/LED/speaker only | Not specified | Not specified | **Yes — WebSocket + Twilio SMS + Firebase push** |
| Physical wave-propagation modeling | Yes (TUNAMI-F1) | No | No | No | No | Yes (Delft3D-FLOW) | No | **No** |
| Coastal wave-height / arrival-time prediction | Yes | No | No | No | No | Yes | No | **No — outputs a categorical risk level, not height/ETA** |
| Offshore sensor / buoy integration | No (seismic only) | Not specified | No | No | Yes (sea-level sensor) | No (simulation) | No | **No (roadmap item — see README §11)** |
| Field validation | Prototype/dashboard | Not specified | Historical replay | None | Yes (Rakata Island, 12%→97% data yield) | Simulation only | Historical replay | **None — unit-tested logic only, not field-deployed** |
| Reproducibility / open code | Not stated | Not stated | Not stated | N/A | Not stated | Not stated | Not stated | **Yes — full source, tests pass, Dockerized** |

---

## 4. Honest positioning

**Where this project is ahead of the reviewed literature:** none of [1]–[7] ship a
complete, runnable, multi-service software stack — they are either simulation
prototypes, notebook-style ML experiments, or architecture proposals. This
project's contribution is squarely **systems engineering**: live public-API
ingestion, a persistent database, a multi-channel alert pipeline, and a real-time
dashboard, all working together and verified to run. That is a meaningfully
different (and complementary) contribution from a forecasting-accuracy paper.

**Where this project is behind the reviewed literature — and should say so in any
report:**
- The risk model is **hand-weighted, not trained**. [3] and [7] fit their models
  to labeled historical tsunami/non-tsunami events; this project's weights are
  engineering estimates. The `MLRiskModel` class exists specifically so this gap
  can be closed by training on the same kind of NOAA NGDC historical dataset [7]
  used, without changing any calling code.
- It does **not model wave physics**. [1] and [6] solve or approximate the
  shallow-water equations to estimate coastal wave height and arrival time — the
  actual quantities disaster responders need. This project only classifies risk
  into four buckets (LOW/MODERATE/HIGH/SEVERE); it cannot tell a responder how
  high the wave will be or when it will arrive at a specific coastline.
- It has **no offshore sensor integration** (no DART buoys, no tide-gauge/IoT
  layer like [5]), so it depends entirely on the USGS/NOAA feeds being timely and
  correct — a single point of failure the buoy-based systems in the literature
  are specifically designed to avoid.
- It has **not been field-validated** — [5] reports a real deployment at Rakata
  Island with measured data-yield improvement; this project has passing unit
  tests and a verified-to-boot API, which is a different and much lower bar than
  field validation against a real coastal sensor network.

**Recommended framing for an academic report:** describe this project as a
*deployable software integration layer for tsunami risk communication* — the
"last mile" that gets USGS/NOAA signals to a live map and to people's phones —
rather than as a novel contribution to tsunami *forecasting science*. Positioned
that way, the comparison table above is a legitimate and defensible gap analysis
rather than an overclaim.

---

## 5. Concrete next steps to close the biggest gaps (in priority order)

1. Train `MLRiskModel` on NOAA's Global Historical Tsunami Database — turns the
   engineered weights in §2 into fitted coefficients, directly comparable to [3]/[7].
2. Add a `distance_to_coast_km` feature (e.g., via a coastline shapefile + point-
   to-line distance) to replace the current `is_offshore=True` placeholder in
   `pipeline.py` with a real geometric check.
3. Add at least one live NOAA CO-OPS tide-station poll (the `fetch_tide_station()`
   function already exists in `noaa_service.py` but isn't wired into the pipeline
   yet) as a second, independent confirmation signal — the same role [5]'s sensor
   plays.
4. If pursuing wave-height/ETA output (matching [1]/[6]), that requires either
   running a real hydrodynamic solver (TUNAMI-F1/Delft3D, heavy) or training a
   surrogate ML model against pre-computed scenarios — a substantially larger
   undertaking than the current classification task, worth scoping as a separate
   phase.
