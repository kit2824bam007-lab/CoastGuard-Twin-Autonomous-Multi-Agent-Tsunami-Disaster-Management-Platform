# Experiment Reproducibility Guide: CoastGuard Twin
**Document Version:** 1.0  
**Target IEEE Submission:** IEEE Conference on Autonomous Systems and Disaster Management  

---

## 1. System Requirements & Environment Setup

- **Operating System:** Windows 10/11, Ubuntu 22.04 LTS, or macOS 13+
- **Python Version:** Python 3.12 (compatible with 3.10+)
- **Node.js Version:** Node.js v18+ (for frontend)

### Installation:
```bash
# Clone the repository
git clone https://github.com/kit2824bam007-lab/CoastGuard-Twin-Autonomous-Multi-Agent-Tsunami-Disaster-Management-Platform.git
cd CoastGuard-Twin-Autonomous-Multi-Agent-Tsunami-Disaster-Management-Platform

# Option A: Local Python Environment
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows PowerShell
# source .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
pip install scipy matplotlib

# Option B: Complete Containerized Stack (Recommended for Full Stack)
cp .env.example .env
docker compose build
docker compose up -d
```

---

## 2. One-Command Experiment & Testing Workflow

Every research claim and software subsystem can be verified via the following standalone scripts:

### Step 1: Execute Automated Test Suite (41 Tests)
```bash
# From workspace root:
# Windows PowerShell:
$env:PYTHONPATH="backend"; python -m pytest backend/tests

# Linux/macOS:
PYTHONPATH=backend pytest backend/tests
```
*Expected Output:* `41 passed in ~60s` (0 failures, 0 errors across all 8 modules)

### Step 2: Reproduce Original Paper Figures
```bash
python backend/app/experiments/reproduce_paper.py
```
*Expected Output:* Confirms 99.44% accuracy, 91.27% macro F1, and traces 50.0% SEVERE recall to $N=2$ test samples. Output: `results/reproduction/reproduction_summary.json`.

### Step 3: Train & Evaluate ML Hazard Classifier
```bash
# Train models
python backend/app/experiments/train_ml.py --mode historical --samples 2400 --seed 42
python backend/app/experiments/train_ml.py --mode calibrated --samples 2400 --seed 42

# Evaluate test sets with sensor noise stress testing
python backend/app/experiments/evaluate_ml.py --mode historical
python backend/app/experiments/evaluate_ml.py --mode calibrated
```
*Expected Output:* Serialized models in `results/models/` and metrics CSV/JSON in `results/classifier/`.

### Step 4: Run Multi-Trial Benchmark Simulation (30 Trials)
```bash
python backend/app/experiments/run_benchmark.py --trials 30 --magnitude 7.8 --distance_km 45.0 --seed 100
```
*Expected Output:* Raw trial records in `results/raw/raw_trials_m7.8_d45.0_n30.csv` and summary metrics with 95% CIs in `results/benchmark/`.

### Step 5: Run Component Ablation Studies (15 Trials per Variant)
```bash
python backend/app/experiments/run_ablation.py --trials 15 --magnitude 7.8 --distance_km 45.0 --seed 200
```
*Expected Output:* Ablation summary CSV and raw trials JSON in `results/ablation/`.

### Step 6: Recalculate Statistical Metrics & Hypothesis Tests
```bash
python backend/app/experiments/analyze_statistics.py
```
*Expected Output:* Recalculates means, medians, IQRs, 95% CIs, Cohen's $d$, paired $t$-tests, and Wilcoxon tests in `results/processed/`.

### Step 7: Run Independent Results Verification Protocol
```bash
python backend/app/experiments/verify_results.py
```
*Expected Output:* Forensic schema and prediction check. Generates `results/verification/verification_report.json`.

### Step 8: Generate Publication-Quality IEEE Figures
```bash
python backend/app/experiments/generate_figures.py
```
*Expected Output:* High-resolution plots exported to `results/figures/`:
- `figure1_benchmark_comparison_errorbars.png`
- `figure2_ablation_component_breakdown.png`
- `figure3_ml_confusion_matrix_heatmap.png`
- `figure4_simulation_bathymetry_hazard_map.png`
