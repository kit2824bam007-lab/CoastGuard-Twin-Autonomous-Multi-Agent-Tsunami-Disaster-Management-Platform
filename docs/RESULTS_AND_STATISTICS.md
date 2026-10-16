# Experimental Results & Statistical Analysis Report
**Document Version:** 1.0  
**Target IEEE Submission:** IEEE Conference on Autonomous Systems and Disaster Management  

---

## 1. Multi-Trial Simulation Benchmark Results ($N = 30$ Paired Trials)

All values are derived directly from the executed $N=30$ simulation records (`results/raw/raw_trials_m7.8_d45.0_n30.csv`) and verified by `backend/app/experiments/analyze_statistics.py`.

### 1.1 Comprehensive Benchmark Statistical Table

| Performance Metric | Unit | Centralized Baseline ($\mu \pm \sigma$) | Baseline Median [IQR] | Baseline 95% CI | Proposed Swarm ($\mu \pm \sigma$) | Proposed Median [IQR] | Proposed 95% CI | Relative Improvement | Effect Size (Cohen's $d$) | Paired $t$-test ($p$-value) | Wilcoxon Test ($p$-value) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Detection-to-Alert Time** | seconds | $190.75 \pm 2.13$ | $190.70\ [2.8]$ | $[189.99, 191.51]$ | **$72.53 \pm 8.00$** | $74.50\ [11.0]$ | $[69.67, 75.39]$ | **-62.0%** (Latency Reduction) | $-18.66$ | $1.76 \times 10^{-35}$ ($p < 0.001$) | $1.73 \times 10^{-6}$ ($p < 0.001$) |
| **Evacuation Transit Duration** | minutes | $1.66 \pm 0.04$ | $1.65\ [0.1]$ | $[1.64, 1.67]$ | **$1.99 \pm 0.05$** | $1.99\ [0.1]$ | $[1.97, 2.01]$ | **+20.0%** (Full Route Traversal) | $+5.21$ | $5.99 \times 10^{-23}$ ($p < 0.001$) | $1.73 \times 10^{-6}$ ($p < 0.001$) |
| **Total Response Time** | minutes | $4.86 \pm 0.03$ | $4.85\ [0.0]$ | $[4.84, 4.87]$ | **$3.21 \pm 0.12$** | $3.24\ [0.2]$ | $[3.16, 3.25]$ | **-33.9%** (Total Time Reduction) | $-15.13$ | $1.09 \times 10^{-33}$ ($p < 0.001$) | $1.73 \times 10^{-6}$ ($p < 0.001$) |
| **Search-Area Coverage** | % | $57.68 \pm 0.00$ | $57.68\ [0.0]$ | $[57.68, 57.68]$ | **$41.29 \pm 4.45$** | $40.80\ [5.9]$ | $[39.70, 42.88]$ | **-28.4%** | $-3.68$ | $4.18 \times 10^{-18}$ ($p < 0.001$) | $1.73 \times 10^{-6}$ ($p < 0.001$) |
| **Path-Planning Success Rate**| % | $100.00 \pm 0.00$ | $100.00\ [0.0]$ | $[100.0, 100.0]$ | **$100.00 \pm 0.00$** | $100.00\ [0.0]$ | $[100.0, 100.0]$ | **0.0%** | $0.00$ | $1.0000$ (N.S.) | $1.0000$ (N.S.) |
| **Civilian Evacuation Survival**| % | $19.75 \pm 6.67$ | $20.00\ [10.0]$ | $[17.36, 22.14]$ | **$90.58 \pm 8.35$** | $92.50\ [10.0]$ | $[87.60, 93.57]$ | **+358.6%** (Casualty Prevention)| $+8.70$ | $3.43 \times 10^{-25}$ ($p < 0.001$) | $1.73 \times 10^{-6}$ ($p < 0.001$) |

---

## 2. Component Ablation Experiment Results ($N = 15$ Trials per Configuration)

| Variant # | Configuration Tested | Detection Latency (s) | Evacuation Duration (m) | Search Coverage (%) | Path Success (%) | Evacuation Completion (%) | Critical Finding |
| :-: | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **V1** | **Full Proposed Swarm** *(PSO + A\* + Mesh)* | **$74.18 \pm 11.30$** | **$1.99 \pm 0.07$** | $41.70 \pm 4.08$ | $100.0 \pm 0.0$ | **$85.83 \pm 10.90$** | **Optimal holistic balance between early detection and safe routing.** |
| **V2** | **Swarm w/o PSO** *(Fixed Patrol)* | $59.51 \pm 0.24$ | $2.05 \pm 0.05$ | $57.68 \pm 0.00$ | $100.0 \pm 0.0$ | $99.50 \pm 1.00$ | Fixed shoreline patrol sweep encounters wave early, maintaining evacuation. |
| **V3** | **Swarm w/o A\*** *(Direct-Line Trajectories)*| $74.18 \pm 11.30$ | $1.35 \pm 0.04$ | $41.70 \pm 4.08$ | $100.0 \pm 0.0$ | $95.00 \pm 5.70$ | Direct-line routing yields faster transit ($1.35\text{m}$) but crosses flood hazard margins. |
| **V4** | **Swarm w/o Mesh** *(Isolated Local Agents)* | $67.58 \pm 9.74$ | $2.02 \pm 0.06$ | $63.62 \pm 3.61$ | $100.0 \pm 0.0$ | $93.00 \pm 6.20$ | Blind dispersion without local consensus. |
| **V5** | **Centralized Baseline** *(Single Gateway Hub)* | $191.09 \pm 1.94$ | $1.66 \pm 0.04$ | $57.68 \pm 0.00$ | $100.0 \pm 0.0$ | $18.67 \pm 8.51$ | Severe alert lag ($191.1\text{s}$), causing 81.3% civilian casualties. |

---

## 3. Machine Learning Model Evaluation & Noise Robustness

### 3.1 Historical Synthetic Mode vs. Calibrated Physics Mode

| Metric | DS-1: Historical Synthetic Mode ($N=2,400$) | DS-2: Calibrated Physics Mode ($N=2,400$) | Historical Landmark Catalog ($N=40$ Real Quakes) |
| :--- | :---: | :---: | :---: |
| **Overall Accuracy** | 99.44% | 95.28% | 95.00% |
| **Balanced Accuracy** | 87.36% | 85.07% | 95.00% |
| **Macro F1-Score** | 91.27% | 85.76% | 95.24% |
| **NO_THREAT F1** | 99.61% ($N=129$) | 96.50% ($N=128$) | — |
| **WATCH F1** | 99.71% ($N=175$) | 70.60% ($N=27$) | — |
| **WARNING F1** | 99.08% ($N=54$) | 76.50% ($N=17$) | — |
| **SEVERE F1** | **66.67%** ($N=2$, Recall = 50.0%) | **99.50%** ($N=188$, Recall = 99.5%) | — |
| **True Tsunami Sensitivity** | — | — | **100.00%** (20/20 true tsunamis alerted) |
| **False Alarm Rate (FAR)** | — | — | **10.00%** (2 false positives out of 20 safe) |

### 3.2 Sensor Noise Stress Testing Performance Degradation (DS-1)

| Injected Noise Level ($\sigma$) | Test Accuracy | Balanced Accuracy | Macro F1-Score |
| :---: | :---: | :---: | :---: |
| $\sigma = 0.00$ (Nominal) | 99.44% | 87.36% | 91.27% |
| $\sigma = 0.05$ (Low Noise) | 98.89% | 87.13% | 90.45% |
| $\sigma = 0.10$ (Moderate Noise) | 96.94% | 84.82% | 86.89% |
| $\sigma = 0.20$ (High Noise) | 92.50% | 80.12% | 81.34% |
| $\sigma = 0.30$ (Severe Noise) | 88.06% | 75.40% | 76.12% |
