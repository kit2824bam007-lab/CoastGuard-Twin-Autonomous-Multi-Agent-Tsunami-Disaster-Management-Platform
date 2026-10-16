# Experimental Protocol: CoastGuard Twin
**Document Version:** 1.0  
**Target IEEE Submission:** IEEE Conference on Autonomous Systems and Disaster Management  

---

## 1. Experimental Objectives & Protocol Principles

The CoastGuard Twin experimental protocol is designed to provide reproducible, statistically rigorous empirical comparisons between:
1. **Centralized Baseline Architecture:** Single central coordinator with communication latency and single point of failure.
2. **Proposed Multi-Agent Swarm System:** Heterogeneous UAV/USV/Ground swarm executing decentralized PSO task allocation, proximity mesh networking, and hazard-aware A* path planning.

### Protocol Integrity Principles:
- **Matched Scenario Pairs:** In every trial $i \in [1, N]$, both architectures receive the identical terrain elevation matrix, initial agent coordinates, civilian distribution, scenario parameters, and pseudo-random seed.
- **Independent Seeds:** Trial seeds vary strictly across trials ($S_i = S_0 + i$).
- **No Discarding of Unfavorable Runs:** All 30 trials are recorded in raw CSVs and included in aggregate analysis.

---

## 2. Benchmark Experiment Protocol (30 Paired Trials)

- **Scenario Configuration:** Standard IEEE Benchmark Scenario (`SCENARIO_M78_D45`)
  - Earthquake Magnitude: $M_w = 7.8$
  - Epicenter Distance to Coast: $D = 45.0\text{ km}$
  - Coastal Terrain: $50 \times 50$ grid ($500\text{m} \times 500\text{m}$)
  - Civilian Population: $N_{\text{civ}} = 40$ placed in vulnerable coastal lowlands ($x \in [21.0, 28.5], y \in [6.0, 44.0]$)
  - Safe Highland Shelter Location: $[x=46.0, y=25.0]$ (Elevation $+85.0\text{m}$)
  - Total Simulation Time: $150$ discrete steps ($\Delta t = 2.0\text{s}$, total duration $300\text{s}$)
  - Number of Paired Trials: $N = 30$ ($S_i = 101, \dots, 130$)
- **Measured Metrics:**
  - `Detection_To_Alert_Time_s`: Elapsed time until first alert confirmation.
  - `Evacuation_Time_min`: Average time for evacuated civilians to reach shelter.
  - `Search_Coverage_pct`: Percentage of $50 \times 50$ cells surveyed by agents.
  - `Path_Planning_Success_pct`: Percentage of A* path queries successfully resolved without encountering impassable flooded cells.
  - `Evacuation_Success_pct`: Percentage of civilian population safely reaching shelter ($d_{\text{inund}} < 1.2\text{m}$ throughout transit).
  - `Communication_Messages`: Total telemetry messages exchanged.

---

## 3. Component Ablation Protocol (15 Trials per Variant)

Five configurations are executed with matched seeds ($S_i = 201, \dots, 215$):
1. **Full Proposed System:** Swarm + PSO + A* + Dynamic Mesh.
2. **Variant w/o PSO:** Agents move via fixed patrol / random walk; tests coverage impact.
3. **Variant w/o A\*:** Agents and civilians move in straight line trajectories; tests obstacle/hazard collision impact.
4. **Variant w/o Mesh:** Agents operate in isolation without neighbor sharing; tests coordination impact.
5. **Centralized Baseline:** All agents report to central hub; tests warning latency and single point of failure impact.

---

## 4. Machine Learning Evaluation Protocol

- **Dataset Splitting:** 70% Train ($N=1,680$), 15% Validation ($N=360$), 15% Test ($N=360$).
- **Stratification:** Stratified across all 4 target classes (`NO_THREAT`, `WATCH`, `WARNING`, `SEVERE`).
- **Leakage Prevention:** Normalization and tree fitting occur exclusively on the training split. Test split remains isolated.
- **Sensor Noise Robustness Protocol:**
  Gaussian noise $\mathcal{N}(0, \sigma^2)$ is injected into continuous telemetry features on the test split:
  $$\sigma \in \{0.00, 0.05, 0.10, 0.20, 0.30\}$$
  Measures accuracy degradation under noisy marine sensor environments.
