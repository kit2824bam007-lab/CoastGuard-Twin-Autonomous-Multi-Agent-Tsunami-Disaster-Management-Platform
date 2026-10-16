# Research Methodology: CoastGuard Twin
**Document Version:** 1.0  
**Target IEEE Submission:** IEEE Conference on Autonomous Systems and Disaster Management  

---

## 1. Problem Formulation & Objective Functions

### 1.1 Disaster Response Optimization Formulation
Let $\mathcal{G} = \mathcal{V} \times \mathcal{E}$ represent the $50 \times 50$ discretized coastal terrain grid, where each cell $u = (x, y) \in \mathcal{V}$ possesses elevation $z(u) \in \mathbb{R}$, time-dependent inundation depth $d_{\text{inund}}(u, t) \in \mathbb{R}^+$, and risk score $\mathcal{R}(u, t) \in [0, 1]$.

A heterogeneous swarm of $N_{\text{agents}}$ agents $\mathcal{A} = \{a_1, \dots, a_N\}$ operates across the grid with positions $\mathbf{x}_i(t) \in \mathcal{V}$ and operational modalities $m_i \in \{\text{UAV}, \text{USV}, \text{GROUND}\}$.

The dual objectives of the multi-agent disaster response platform are:
1. **Minimize Detection-to-Alert Latency ($T_{\text{alert}}$):**
   $$T_{\text{alert}} = \min \{ t \mid \exists a_i \in \mathcal{A}, d_{\text{inund}}(\mathbf{x}_i(t), t) > \theta_{\text{detect}} \lor \text{Anomaly}(\mathbf{x}_i(t)) > \theta_{\text{sensor}} \}$$
2. **Maximize Civilian Population Survival Rate ($\mathcal{S}_{\text{evac}}$):**
   $$\mathcal{S}_{\text{evac}} = \frac{1}{|\mathcal{C}|} \sum_{c \in \mathcal{C}} \mathbb{I} \Big[ \|\mathbf{x}_c(T_{\text{end}}) - \mathbf{x}_{\text{shelter}}\|_2 \le \epsilon \land \forall t \le T_{\text{end}}, d_{\text{inund}}(\mathbf{x}_c(t), t) < D_{\text{lethal}} \Big]$$
   Where $\mathcal{C}$ is the civilian population, $\mathbb{I}[\cdot]$ is the indicator function, and $D_{\text{lethal}} = 1.2\text{ meters}$.

---

## 2. Algorithmic Formulations

### 2.1 Particle Swarm Optimization (PSO) Task Allocation
Each agent updates velocity $\mathbf{v}_i(t) = [v_{x,i}(t), v_{y,i}(t)]^T$ and position $\mathbf{x}_i(t) = [x_i(t), y_i(t)]^T$:

$$\mathbf{v}_i(t+1) = w \mathbf{v}_i(t) + c_1 r_1 (\mathbf{p}_i - \mathbf{x}_i(t)) + c_2 r_2 (\mathbf{g}_i(t) - \mathbf{x}_i(t))$$

$$\mathbf{x}_i(t+1) = \mathbf{x}_i(t) + \mathbf{v}_i(t+1)$$

- **Hyperparameters:** Inertia $w = 0.5$, cognitive acceleration $c_1 = 1.2$, social acceleration $c_2 = 1.5$.
- **Objective Function / Fitness:**
  $$\text{Fitness}(\mathbf{x}) = \lambda_1 \cdot \text{Unsurveyed}(\mathbf{x}) + \lambda_2 \cdot \mathcal{R}(\mathbf{x}, t) - \lambda_3 \cdot \min_{j \ne i} \|\mathbf{x} - \mathbf{x}_j\|_2^{-1}$$
  Favors unexplored cells and active hazard zones while penalizing swarm clustering.
- **Velocity Clamping:**
  $$\|\mathbf{v}_i(t+1)\|_2 \le v_{\max}(m_i), \quad v_{\max} = \begin{cases} 1.8\text{ units/s} & m_i = \text{UAV} \\ 1.0\text{ units/s} & m_i = \text{USV} \\ 0.7\text{ units/s} & m_i = \text{GROUND} \end{cases}$$

### 2.2 8-Connected Hazard-Aware A\* Path Planning
Path search from source $s$ to destination $g$ computes $f(n) = g(n) + h(n)$ with Octile distance heuristic:
$$h(n) = 1.0 \cdot (|x - x_g| + |y - y_g|) + (\sqrt{2} - 2.0) \min(|x - x_g|, |y - y_g|)$$

Edge cost between adjacent cells $n \to n'$:
$$c(n, n') = \Delta d \cdot \Big[ 1.0 + \alpha \max(0, z(n') - z(n)) + \beta d_{\text{inund}}(n') + \gamma \mathcal{R}(n') \Big]$$
Where $\alpha = 0.02, \beta = 10.0, \gamma = 5.0$, and edge is blocked ($c = \infty$) if:
- $z(n') \le 0$ for GROUND/CIVILIAN agents
- $d_{\text{inund}}(n') \ge 1.5\text{m}$ for GROUND/CIVILIAN agents
- $z(n') > 0 \land d_{\text{inund}}(n') < 0.8\text{m}$ for USV agents

---

## 3. Centralized Baseline Definition & Experimental Rules

To ensure a fair and scientifically defensible comparison:
1. **Identical Inputs:** Both architectures receive the identical bathymetric grid, earthquake magnitude ($M_w=7.8$), epicenter distance ($45\text{ km}$), initial agent positions, civilian coordinates, and pseudo-random seed.
2. **Centralized Gateway Constraints:**
   - Single central dispatcher node at $[x=48, y=25]$.
   - Telemetry must be polled sequentially across agents (central communication bottleneck).
   - Verification delay: Nominal alert latency has a base delay of $145.0\text{ s}$ before public sirens/shelter guidance are triggered.
   - If an agent fails, central controller incurs a timeout delay before detecting loss and reallocating search.
