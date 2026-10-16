# Dataset Provenance & Data Integrity Report: CoastGuard Twin
**Document Version:** 1.0  
**Target IEEE Submission:** IEEE Conference on Autonomous Systems and Disaster Management  

---

## 1. Summary of Datasets Used in the Research

CoastGuard Twin utilizes three distinct datasets for evaluation, modeling, and real-time ingestion:

| Dataset Identifier | Nature of Data | Sample Size | Primary Purpose in Research | Data Source / License | Circular Labeling Risk? |
| :--- | :--- | :---: | :--- | :--- | :---: |
| **DS-1: Synthetic Hazard Tabular Dataset** | Purely Synthetic (Exponential & Uniform) | 2,400 samples | Historical reproduction of Random Forest classifier | Internal generator (`ml_classifier.py`) | **High (Threshold-based labels derived from features)** |
| **DS-2: Calibrated Physics Dataset** | Synthetic with Physical Probabilities & Noise | 2,400 samples | Rigorous ML benchmark evaluation with noise perturbation | Internal generator (`train_ml.py`) | Low (Probabilistic continuous scoring with Gaussian noise) |
| **DS-3: Historical Landmark Catalog** | Real Curated Observational Earthquakes | 40 events | Historical validation & backtesting of risk models | NOAA NGDC / USGS public archives | **Zero (Real historical observations)** |
| **DS-4: Live USGS & NOAA Feeds** | Real-time Public Ingestion | Continuous stream | Live prototype alerting demonstrations | USGS Earthquake API / NOAA PTWC Atom Feed | Zero (External public domain) |

---

## 2. Dataset DS-1: Synthetic Hazard Tabular Dataset (Historical Baseline)

- **Generation Code:** `backend/app/services/ml_classifier.py` (`_generate_synthetic_dataset`)
- **Features (6):**
  1. `p_wave`: Primary seismic waveform amplitude ($\text{Exp}(\lambda=10.0)$), unit: m/s².
  2. `s_wave`: Secondary seismic waveform amplitude ($\text{Exp}(\lambda=5.0)$), unit: m/s².
  3. `buoy_anomaly`: Ocean sea-level anomaly ($\text{Exp}(\lambda=2.5)$), unit: meters.
  4. `shoreline_code`: Categorical integer ($0=\text{NORMAL}, 1=\text{RECEDING}, 2=\text{SURGING}$).
  5. `max_inundation_m`: Projected coastal flood depth ($\max(0, 1.5 \cdot \text{buoy\_anomaly} - \mathcal{U}(0, 1))$), unit: meters.
  6. `distance_km`: Epicenter distance to coastal line ($\mathcal{U}(10.0, 200.0)$), unit: km.
- **Label Generation Rules:**
  - `label = 3` (`SEVERE`): `buoy_anomaly > 1.8` or `max_inundation > 2.5` or (`s_wave > 1.5` and `shoreline_code == 2`)
  - `label = 2` (`WARNING`): `buoy_anomaly > 0.8` or `max_inundation > 1.0` or `s_wave > 0.8`
  - `label = 1` (`WATCH`): `buoy_anomaly > 0.3` or `s_wave > 0.3` or `shoreline_code == 1`
  - `label = 0` (`NO_THREAT`): Otherwise
- **Data Leakage & Circularity Disclosure:**
  Because the target class is deterministically computed from if-else thresholds on the exact input features, the Random Forest's 99.4% accuracy is a reflection of decision-tree rule reconstruction, not generalized physical forecasting. This must be transparently stated in IEEE submissions.
- **Class Distribution ($N=2,400$):**
  `NO_THREAT`: 860 (35.8%), `WATCH`: 1,168 (48.7%), `WARNING`: 359 (15.0%), `SEVERE`: **13 (0.54%)**.

---

## 3. Dataset DS-3: Landmark Historical Earthquake Catalog

- **Catalog Location:** Documented in `docs/backtest_report.md`
- **Catalog Size:** 40 landmark historical earthquakes (20 tsunamigenic, 20 non-tsunamigenic controls)
- **Traceable Real Historical Events (Examples):**
  - **Tohoku, Japan (2011):** $M_w=9.0$, Depth = 24 km, Offshore $\to$ True Label = 1 (Tsunami)
  - **Sumatra-Andaman (2004):** $M_w=9.1$, Depth = 30 km, Offshore $\to$ True Label = 1 (Tsunami)
  - **Maule, Chile (2010):** $M_w=8.8$, Depth = 35 km, Offshore $\to$ True Label = 1 (Tsunami)
  - **Sichuan, China (2008):** $M_w=7.9$, Depth = 19 km, Inland $\to$ True Label = 0 (Control)
  - **Nepal (2015):** $M_w=7.8$, Depth = 15 km, Inland $\to$ True Label = 0 (Control)
  - **Fiji (2018):** $M_w=8.2$, Depth = 563 km, Deep Sea $\to$ True Label = 0 (Control: deep mantle, no sea-floor displacement)
  - **Sea of Okhotsk (2013):** $M_w=8.3$, Depth = 609 km, Deep Sea $\to$ True Label = 0 (Control)
- **Backtesting Performance:**
  - Accuracy: **95.00%** (38/40 correct)
  - Sensitivity / Recall: **100.00%** (20/20 true tsunamis alerted)
  - False Alarm Rate: **10.00%** (2 false positives: Wharton Basin 2012 and Gulf of Alaska 2018, both high-magnitude strike-slip faults).
