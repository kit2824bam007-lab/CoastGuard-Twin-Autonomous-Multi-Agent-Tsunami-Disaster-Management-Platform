# Historical Model Validation & Backtest Report

This validation report evaluates the accuracy of the **Rule-Based Risk Model** and the **Machine Learning Risk Model** against a manually compiled catalog of **40 landmark historical earthquakes** (including 20 famous tsunamigenic and 20 non-tsunamigenic control cases).

*   **Active ML Mode during execution:** ML Model (ACTIVE)

---

## 1. Summary Performance Metrics

| Metric | Rule-Based Model (MVP) | Machine Learning Model (RF) | Description |
| :--- | :---: | :---: | :--- |
| **Accuracy** | 87.50% | 95.00% | Overall correct forecasts / total catalog |
| **Precision** | 80.00% | 90.91% | Fraction of issued alerts that were true tsunamis |
| **Recall (Sensitivity)** | 100.00% | 100.00% | Fraction of actual tsunamis correctly alerted |
| **F1-Score** | 88.89% | 95.24% | Harmonic mean of precision and recall |
| **False Alarm Rate (FAR)** | 25.00% | 10.00% | Fraction of safe events that triggered false alerts |

---

## 2. Confusion Matrices

### Rule-Based Model
*   **True Positives (TP):** 20
*   **False Positives (FP):** 5 (Fiji 2018, Sea of Okhotsk 2013, Wharton Basin 2012, Lombok 2018, Gulf of Alaska 2018)
*   **True Negatives (TN):** 15
*   **False Negatives (FN):** 0

### Machine Learning Model (RF)
*   **True Positives (TP):** 20
*   **False Positives (FP):** 2 (Wharton Basin 2012, Gulf of Alaska 2018 - *due to strike-slip faulting which requires focal mechanism modeling*)
*   **True Negatives (TN):** 18
*   **False Negatives (FN):** 0

---

## 3. Detailed Historical Catalog Run Results

Below are the individual evaluation rows for both models:

| Event Name | M | Depth (km) | Land/Sea | True | Rule Pred | ML Pred (Score) | Status (Rule/ML) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Valdivia, Chile (1960) | 9.5 | 33 | Sea | **1** | SEVERE | SEVERE (0.97) | `TP` / `TP` |
| Prince William Sound, Alaska (1964) | 9.2 | 25 | Sea | **1** | SEVERE | SEVERE (0.98) | `TP` / `TP` |
| Sumatra-Andaman (2004) | 9.1 | 30 | Sea | **1** | SEVERE | SEVERE (0.97) | `TP` / `TP` |
| Tohoku, Japan (2011) | 9.0 | 24 | Sea | **1** | SEVERE | SEVERE (0.98) | `TP` / `TP` |
| Maule, Chile (2010) | 8.8 | 35 | Sea | **1** | SEVERE | SEVERE (0.96) | `TP` / `TP` |
| Nias, Indonesia (2005) | 8.6 | 30 | Sea | **1** | SEVERE | SEVERE (0.96) | `TP` / `TP` |
| Samoa (2009) | 8.1 | 18 | Sea | **1** | SEVERE | SEVERE (0.94) | `TP` / `TP` |
| Fukushima, Japan (2022) | 7.4 | 57 | Sea | **1** | HIGH | HIGH (0.76) | `TP` / `TP` |
| Hokkaido, Japan (2003) | 8.3 | 27 | Sea | **1** | SEVERE | SEVERE (0.95) | `TP` / `TP` |
| Illapel, Chile (2015) | 8.3 | 22 | Sea | **1** | SEVERE | SEVERE (0.95) | `TP` / `TP` |
| Solomon Islands (2013) | 8.0 | 28 | Sea | **1** | SEVERE | SEVERE (0.93) | `TP` / `TP` |
| Mentawai, Indonesia (2010) | 7.8 | 20 | Sea | **1** | SEVERE | SEVERE (0.90) | `TP` / `TP` |
| Queen Charlotte, Canada (2012) | 7.8 | 14 | Sea | **1** | SEVERE | SEVERE (0.91) | `TP` / `TP` |
| Iquique, Chile (2014) | 8.2 | 25 | Sea | **1** | SEVERE | SEVERE (0.94) | `TP` / `TP` |
| Kaikoura, New Zealand (2016) | 7.8 | 15 | Sea | **1** | SEVERE | SEVERE (0.91) | `TP` / `TP` |
| Palu, Indonesia (2018) | 7.5 | 20 | Sea | **1** | SEVERE | HIGH (0.84) | `TP` / `TP` |
| Kaikoura, New Zealand (2016) | 7.8 | 15 | Sea | **1** | SEVERE | SEVERE (0.91) | `TP` / `TP` |
| Kermadec Islands, NZ (2021) | 8.1 | 19 | Sea | **1** | SEVERE | SEVERE (0.94) | `TP` / `TP` |
| Chignik, Alaska (2021) | 8.2 | 32 | Sea | **1** | SEVERE | SEVERE (0.94) | `TP` / `TP` |
| Java, Indonesia (2006) | 7.7 | 34 | Sea | **1** | SEVERE | HIGH (0.87) | `TP` / `TP` |
| Hualien, Taiwan (2024) | 7.4 | 34 | Sea | **1** | SEVERE | HIGH (0.81) | `TP` / `TP` |
| Sichuan, China (2008) | 7.9 | 19 | Land | **0** | LOW | LOW (0.01) | `TN` / `TN` |
| Nepal (2015) | 7.8 | 15 | Land | **0** | LOW | LOW (0.01) | `TN` / `TN` |
| Kahramanmaras, Turkey (2023) | 7.8 | 10 | Land | **0** | LOW | LOW (0.01) | `TN` / `TN` |
| Kobe, Japan (1995) | 6.9 | 16 | Land | **0** | LOW | LOW (0.00) | `TN` / `TN` |
| Kumamoto, Japan (2016) | 7.0 | 10 | Land | **0** | LOW | LOW (0.00) | `TN` / `TN` |
| Loma Prieta, USA (1989) | 6.9 | 19 | Land | **0** | LOW | LOW (0.00) | `TN` / `TN` |
| Cianjur, Indonesia (2022) | 5.6 | 10 | Land | **0** | LOW | LOW (0.00) | `TN` / `TN` |
| Bam, Iran (2003) | 6.6 | 10 | Land | **0** | LOW | LOW (0.00) | `TN` / `TN` |
| Fiji (2018) | 8.2 | 563 | Sea | **0** | HIGH | LOW (0.03) | `FP` / `TN` |
| Sea of Okhotsk (2013) | 8.3 | 609 | Sea | **0** | HIGH | LOW (0.03) | `FP` / `TN` |
| Mariana Islands (2016) | 7.9 | 212 | Sea | **0** | MODERATE | LOW (0.04) | `TN` / `TN` |
| Bonin Islands, Japan (2015) | 7.8 | 680 | Sea | **0** | MODERATE | LOW (0.02) | `TN` / `TN` |
| Wharton Basin (2012) | 8.6 | 20 | Sea | **0** | SEVERE | SEVERE (0.94) | `FP` / `FP` |
| Lombok, Indonesia (2018) | 6.9 | 10 | Sea | **0** | HIGH | MODERATE (0.34) | `FP` / `TN` |
| Gulf of Alaska (2018) | 7.9 | 14 | Sea | **0** | SEVERE | HIGH (0.64) | `FP` / `FP` |
| Fukushima Inland (2015) | 5.3 | 40 | Land | **0** | LOW | LOW (0.00) | `TN` / `TN` |
| Tokyo Bay (2015) | 5.2 | 57 | Sea | **0** | LOW | LOW (0.01) | `TN` / `TN` |
| Offshore Oregon (2021) | 5.8 | 10 | Sea | **0** | MODERATE | LOW (0.05) | `TN` / `TN` |
| Java coast minor (2021) | 6.1 | 80 | Sea | **0** | MODERATE | LOW (0.03) | `TN` / `TN` |
| Christchurch, NZ (2011) | 6.2 | 5 | Land | **0** | LOW | LOW (0.00) | `TN` / `TN` |
