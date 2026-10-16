# Experimental Results Reproduction Report: CoastGuard Twin
**Document Version:** 1.0  
**Target IEEE Submission:** IEEE Conference on Autonomous Systems and Disaster Management  
**Date of Reproduction:** October 2026  
**Execution Environment:** Windows 11, Python 3.12.7, Scikit-learn 1.6+  
**Reproduction Script:** `backend/app/experiments/reproduce_paper.py`

---

## 1. Executive Summary

This report documents the reproduction of all empirical figures and benchmarks originally reported in the CoastGuard Twin research paper draft and repository documentation. Each result was tested by running the original codebase with its historical configuration.

### Summary of Verdict:
- **ML Classifier Results:** **REPRODUCED WITH CRITICAL METHODOLOGICAL CONTEXT.** The exact numbers (99.4% accuracy, 91.3% macro F1, 50.0% SEVERE recall) are reproduced using the original script. However, the reproduction revealed that the 50.0% recall on the `SEVERE` class is an artifact of severe class imbalance ($N=2$ test samples), and the 99.4% overall accuracy is driven by circular threshold-based label generation.
- **Tsunami Simulation Benchmark:** **REPRODUCED AS MOCKED RANDOM GENERATION.** The paper's benchmark numbers (80.8% latency reduction, 49.7% evacuation reduction, 61.7% search coverage increase, 34.8% path-planning success increase) were reproduced as outputs of a random distribution generator centered around hardcoded constants in `benchmark_service.py`. They did not originate from dynamic agent simulations.

---

## 2. Reproduction Results Table

| Metric Name | Value Reported in Paper | Source File & Function | Formula & Baseline Comparison | Reproduced? | Reproduced Value (Measured) | Difference (Reported vs Reproduced) | Unresolved Discrepancy & Root Cause |
| :--- | :---: | :--- | :--- | :---: | :---: | :---: | :--- |
| **Dataset Size** | 2,400 samples | `backend/app/services/ml_classifier.py` (`_generate_synthetic_dataset`) | Synthetic generation with fixed seed 42 | **YES** | 2,400 samples | 0 (Exact) | None. Fixed sample size. |
| **RF Accuracy** | 99.4% | `ml_classifier.py` (`_train_initial_model`) | $\frac{\text{TP} + \text{TN}}{\text{Total}}$ on 15% test split ($N=360$) | **YES** | 99.44% | +0.04% | None. Labels are direct threshold logic on features. |
| **Macro F1-Score** | 91.3% | `ml_classifier.py` (`_train_initial_model`) | $\frac{1}{4} \sum_{c=1}^4 \text{F1}_c$ | **YES** | 91.27% | -0.03% | None. Harmonic mean across 4 classes. |
| **SEVERE Class Recall** | 50.0% | `ml_classifier.py` (`_train_initial_model`) | $\frac{\text{TP}}{\text{TP} + \text{FN}}$ for Class 3 (`SEVERE`) | **YES** | 50.00% | 0.00% (Exact) | **Class Imbalance Artifact:** The test set contained only **2** severe instances. $\text{TP}=1, \text{FN}=1 \implies \frac{1}{2}=50\%$. |
| **Detection-to-Alert Latency Reduction** | 80.8% | `backend/app/services/benchmark_service.py` (`_generate_benchmark_comparison`) | $\frac{\text{Base} - \text{Swarm}}{\text{Base}} \times 100$, Base ~ 156s, Swarm ~ 32s | **YES (Range)** | 79.4% (Range: 76.0% – 82.4%) | -1.4% (Mean) | **Mocked Generator:** Value was drawn from `random.uniform()` around hardcoded offsets rather than an agent simulation. |
| **Evacuation Time Reduction** | 49.7% | `benchmark_service.py` (`_generate_benchmark_comparison`) | $\frac{\text{Base} - \text{Swarm}}{\text{Base}} \times 100$, Base ~ 38.5m, Swarm ~ 19.2m | **YES (Range)** | 50.5% (Range: 42.1% – 57.7%) | +0.8% (Mean) | **Mocked Generator:** Static heuristic formulas without dynamic civilian agents. |
| **Search Coverage Increase** | 61.7% | `benchmark_service.py` (`_generate_benchmark_comparison`) | $\frac{\text{Swarm} - \text{Base}}{\text{Base}} \times 100$, Base ~ 62.4%, Swarm ~ 96.8% | **YES (Range)** | 55.1% (Range: 46.1% – 67.7%) | -6.6% (Mean) | **Mocked Generator:** Synthetic formula. If calculated as $\frac{96.8 - 62.4}{62.4} \times 100 = 55.1\%$, whereas $96.8 - 62.4 = 34.4$ percentage points. The 61.7% reported in the paper is an individual seed draw from this uniform distribution. |
| **Path-Planning Success Increase** | 34.8% | `benchmark_service.py` (`_generate_benchmark_comparison`) | $\frac{\text{Swarm} - \text{Base}}{\text{Base}} \times 100$, Base ~ 74.2%, Swarm ~ 98.4% | **YES (Range)** | 32.1% (Range: 24.6% – 42.3%) | -2.7% (Mean) | **Mocked Generator:** Derived from static random ranges. |

---

## 3. Deep-Dive: Machine Learning Classifier Evaluation

### 3.1 Per-Class Breakdown and Raw Confusion Matrix

The exact confusion matrix on the 360-sample test set ($15\%$ of 2,400) is:

```
Actual \ Predicted       NO_THREAT    WATCH    WARNING    SEVERE    Total (Support)
NO_THREAT                   129         0         0         0             129
WATCH                         1       174         0         0             175
WARNING                       0         0        54         0              54
SEVERE                        0         0         1         1               2
Total Predicted             130       174        55         1             360
```

### 3.2 Metrics per Class

| Class | Support | Precision | Recall | F1-Score | Analysis |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **NO_THREAT** | 129 | 99.23% | 100.00% | 99.61% | Cleanly separated when features are below lowest thresholds. |
| **WATCH** | 175 | 100.00% | 99.43% | 99.71% | 1 false negative misclassified as NO_THREAT due to marginal boundary. |
| **WARNING** | 54 | 98.18% | 100.00% | 99.08% | Captures all 54 actual WARNING samples, plus 1 false positive from SEVERE. |
| **SEVERE** | **2** | **100.00%** | **50.00%** | **66.67%** | **Severe class under-representation.** Of the 2 samples, 1 is predicted as WARNING. |

### 3.3 Root Cause of the 50.0% SEVERE Recall
The dataset generator samples `buoy_anomaly` from an exponential distribution with rate parameter $\beta=0.4$:
$$f(x) = \frac{1}{0.4} e^{-x / 0.4}$$
To qualify as `SEVERE`, the rule requires $\text{buoy\_anomaly} > 1.8$, which occurs with probability:
$$P(X > 1.8) = e^{-1.8 / 0.4} = e^{-4.5} \approx 0.0111 \quad (1.11\%)$$
Across 2,400 samples, the expected number of SEVERE examples is $2400 \times 0.0111 \approx 26.6$. In the actual run with random seed 42, only 13 total samples satisfied the condition across the entire dataset. In the test split (15%), exactly 2 samples were assigned to SEVERE.

**Scientific Finding:** Reporting 50% recall gives reviewers the impression of an algorithm failing 50% of the time on a substantial validation sample. In reality, it was a single misclassified sample ($1 / 2$).

---

## 4. Deep-Dive: Tsunami Benchmark Mocking

In `backend/app/services/benchmark_service.py`, lines 24–33:
```python
base_detection_time = round(145.0 + random.uniform(-10.0, 15.0) + (10.0 - event_magnitude) * 5.0, 1)
base_evac_time = round(38.5 + random.uniform(-3.0, 5.0), 1)
base_coverage = round(62.4 + random.uniform(-4.0, 4.0), 1)
base_path_success = round(74.2 + random.uniform(-5.0, 5.0), 1)

swarm_detection_time = round(32.0 + random.uniform(-3.0, 4.0), 1)
swarm_evac_time = round(19.2 + random.uniform(-1.5, 2.0), 1)
swarm_coverage = round(96.8 + random.uniform(-1.5, 1.5), 1)
swarm_path_success = round(98.4 + random.uniform(-1.0, 1.0), 1)
```

**Scientific Finding:**
The reported improvements (80.8%, 49.7%, 61.7%, 34.8%) were not produced by running multi-agent swarm algorithms or comparing them against a simulated centralized coordinator. They were generated by calculating percentage differences between random values drawn around static offsets.

---

## 5. Remediation Mandate

To make the research scientifically credible and defensible for IEEE review:
1. **Preserve Historical Numbers:** Document them clearly as "Original Reported Heuristic Baseline / Prototype Results".
2. **Implement Genuine Simulation Engines:**
   - Real A* path planning over bathymetric/inundation hazard obstacles.
   - Dynamic civilian agent evacuation over the 50x50 coastal grid toward shelters.
   - Genuine centralized baseline system suffering from single-gateway polling bottlenecks.
3. **Run Multi-Trial Experiments ($N \ge 30$):**
   - Record raw trial values, means, standard deviations, and 95% confidence intervals.
   - Provide complete CSV/JSON raw data exports.
