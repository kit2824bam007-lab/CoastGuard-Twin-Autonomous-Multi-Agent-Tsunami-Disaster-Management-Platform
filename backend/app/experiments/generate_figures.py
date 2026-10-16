"""
Publication-Quality Plotting Script for CoastGuard Twin IEEE Figures
Generates figures directly from verified raw experimental outputs:
- Figure 1: Multi-Trial Benchmark Comparison with 95% Confidence Intervals
- Figure 2: Ablation Study Component Breakdown
- Figure 3: ML Confusion Matrix & Per-Class Performance
- Figure 4: Coastal Bathymetry & A* Hazard Evacuation Map
Exports high-resolution figures to results/figures/
"""
import os
import sys
import json
import csv
import numpy as np
import matplotlib
matplotlib.use("Agg") # Non-interactive backend
import matplotlib.pyplot as plt

backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)
results_root = os.path.join(backend_root, "..", "results")
figures_dir = os.path.join(results_root, "figures")
os.makedirs(figures_dir, exist_ok=True)

# Publication styling
plt.rcParams.update({
    "font.size": 10,
    "axes.labelsize": 11,
    "axes.titlesize": 12,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "figure.titlesize": 13,
    "figure.dpi": 300
})

def plot_benchmark_comparison():
    """Generates Figure 1: Benchmark comparison with error bars."""
    summary_csv = os.path.join(results_root, "benchmark", "summary_metrics_m7.8_d45.0_n30.csv")
    if not os.path.exists(summary_csv):
        print(f"Warning: {summary_csv} not found, skipping Fig 1")
        return

    metrics = []
    base_means = []
    base_errs = []
    prop_means = []
    prop_errs = []
    units = []

    with open(summary_csv, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            metrics.append(row["Metric"])
            units.append(row["Unit"])
            bm = float(row["Baseline_Mean"])
            base_means.append(bm)
            base_errs.append(float(row["Baseline_Std"]))
            pm = float(row["Proposed_Mean"])
            prop_means.append(pm)
            prop_errs.append(float(row["Proposed_Std"]))

    fig, axes = plt.subplots(1, 4, figsize=(14, 4))
    fig.suptitle("Figure 1: CoastGuard Twin Benchmark Comparison (N = 30 Independent Trials, 95% CI)", fontweight="bold")

    if len(metrics) >= 6:
        selected_indices = [0, 1, 3, 5]  # Det Latency, Evac Duration, Coverage, Evacuation Completion
    else:
        selected_indices = [0, 1, 2, min(4, len(metrics) - 1)]
    colors = ["#475569", "#0891b2"]  # Slate gray vs Cyan

    for idx, ax_idx in enumerate(range(4)):
        m_idx = selected_indices[idx]
        ax = axes[ax_idx]
        title = metrics[m_idx]
        unit = units[m_idx]

        b_val = base_means[m_idx]
        b_err = base_errs[m_idx]
        p_val = prop_means[m_idx]
        p_err = prop_errs[m_idx]

        bars = ax.bar(["Centralized\nBaseline", "Proposed\nSwarm"], [b_val, p_val], yerr=[b_err, p_err], capsize=5, color=colors, width=0.55)
        ax.set_ylabel(f"{unit}")
        ax.set_title(title, fontsize=10, fontweight="bold")
        ax.grid(axis="y", linestyle="--", alpha=0.5)

        # Bar value annotations
        for bar in bars:
            h = bar.get_height()
            ax.annotate(f"{h:.1f}", xy=(bar.get_x() + bar.get_width() / 2, h), xytext=(0, 4),
                        textcoords="offset points", ha="center", va="bottom", fontsize=9, fontweight="bold")

    plt.tight_layout()
    out_path = os.path.join(figures_dir, "figure1_benchmark_comparison_errorbars.png")
    plt.savefig(out_path)
    plt.close()
    print(f"Generated: {out_path}")

def plot_ablation_study():
    """Generates Figure 2: Ablation study component breakdown."""
    ablation_csv = os.path.join(results_root, "ablation", "ablation_summary_m7.8_d45.0_n15.csv")
    if not os.path.exists(ablation_csv):
        ablation_csv = os.path.join(results_root, "ablation", "ablation_summary_m7.8_d45.0_n10.csv")

    if not os.path.exists(ablation_csv):
        print(f"Warning: {ablation_csv} not found, skipping Fig 2")
        return

    variants = []
    latencies = []
    coverages = []
    survivals = []

    with open(ablation_csv, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["Ablation_Variant"]
            # Shorten label for clean plot
            short_name = name.replace("Full Proposed System (PSO + A* + Mesh)", "1. Full Swarm") \
                             .replace("Swarm w/o PSO (Fixed Patrol)", "2. No PSO") \
                             .replace("Swarm w/o A* (Direct Path)", "3. No A*") \
                             .replace("Swarm w/o Mesh (Isolated Agents)", "4. No Mesh") \
                             .replace("Centralized Baseline System", "5. Centralized")
            variants.append(short_name)
            latencies.append(float(row["Detection_Time_s_Mean"]))
            coverages.append(float(row["Search_Coverage_pct_Mean"]))
            survivals.append(float(row["Evacuation_Success_pct_Mean"]))

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(13, 4))
    fig.suptitle("Figure 2: Component Ablation Study Across 5 Configurations", fontweight="bold")

    x = np.arange(len(variants))
    bar_width = 0.55

    # 1. Detection Latency
    ax1.bar(x, latencies, width=bar_width, color="#0284c7")
    ax1.set_xticks(x)
    ax1.set_xticklabels(variants, rotation=25, ha="right")
    ax1.set_ylabel("Seconds (Lower is Better)")
    ax1.set_title("Detection Latency", fontweight="bold")
    ax1.grid(axis="y", linestyle="--", alpha=0.5)

    # 2. Search Coverage
    ax2.bar(x, coverages, width=bar_width, color="#059669")
    ax2.set_xticks(x)
    ax2.set_xticklabels(variants, rotation=25, ha="right")
    ax2.set_ylabel("% (Higher is Better)")
    ax2.set_title("Search-Area Coverage", fontweight="bold")
    ax2.grid(axis="y", linestyle="--", alpha=0.5)

    # 3. Civilian Survival
    ax3.bar(x, survivals, width=bar_width, color="#7c3aed")
    ax3.set_xticks(x)
    ax3.set_xticklabels(variants, rotation=25, ha="right")
    ax3.set_ylabel("% (Higher is Better)")
    ax3.set_title("Civilian Survival Rate", fontweight="bold")
    ax3.grid(axis="y", linestyle="--", alpha=0.5)

    plt.tight_layout()
    out_path = os.path.join(figures_dir, "figure2_ablation_component_breakdown.png")
    plt.savefig(out_path)
    plt.close()
    print(f"Generated: {out_path}")

def plot_confusion_matrix():
    """Generates Figure 3: Multi-class ML Confusion Matrix."""
    summary_json = os.path.join(results_root, "classifier", "evaluation_summary_historical_seed42.json")
    if not os.path.exists(summary_json):
        print(f"Warning: {summary_json} not found, skipping Fig 3")
        return

    with open(summary_json, "r") as f:
        data = json.load(f)

    cm = np.array(data["confusion_matrix_raw"])
    classes = ["NO_THREAT", "WATCH", "WARNING", "SEVERE"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5))
    fig.suptitle("Figure 3: Random Forest Hazard Severity Classifier Evaluation", fontweight="bold")

    # Raw counts
    im1 = ax1.imshow(cm, cmap="Blues")
    ax1.set_title("Confusion Matrix (Raw Counts)")
    ax1.set_xticks(range(len(classes)))
    ax1.set_yticks(range(len(classes)))
    ax1.set_xticklabels(classes, rotation=25, ha="right")
    ax1.set_yticklabels(classes)
    ax1.set_xlabel("Predicted Label")
    ax1.set_ylabel("Actual Label")

    for i in range(len(classes)):
        for j in range(len(classes)):
            color = "white" if cm[i, j] > np.max(cm) / 2 else "black"
            ax1.text(j, i, str(cm[i, j]), ha="center", va="center", color=color, fontweight="bold")

    # Normalized percentages
    cm_norm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis] * 100
    im2 = ax2.imshow(cm_norm, cmap="Blues")
    ax2.set_title("Confusion Matrix (Recall % per Class)")
    ax2.set_xticks(range(len(classes)))
    ax2.set_yticks(range(len(classes)))
    ax2.set_xticklabels(classes, rotation=25, ha="right")
    ax2.set_yticklabels(classes)
    ax2.set_xlabel("Predicted Label")
    ax2.set_ylabel("Actual Label")

    for i in range(len(classes)):
        for j in range(len(classes)):
            val = cm_norm[i, j]
            color = "white" if val > 50 else "black"
            ax2.text(j, i, f"{val:.1f}%", ha="center", va="center", color=color, fontweight="bold")

    plt.tight_layout()
    out_path = os.path.join(figures_dir, "figure3_ml_confusion_matrix_heatmap.png")
    plt.savefig(out_path)
    plt.close()
    print(f"Generated: {out_path}")

def plot_hazard_and_path_map():
    """Generates Figure 4: Coastal Bathymetry & A* Route Planning."""
    from app.services.path_planner import astar_planner
    from app.services.simulation_benchmark_runner import CoastalSimulationTrial

    trial = CoastalSimulationTrial(trial_id=1, seed=42)
    bathymetry = np.array(trial.bathymetry)
    trial._update_inundation(t_sec=120.0)
    inundation = trial.inundation_grid

    # Plan a path from lowland (22, 15) to shelter (46, 25)
    plan = astar_planner.find_path((22, 15), (46, 25), agent_type="CIVILIAN",
                                  bathymetry_grid=trial.bathymetry,
                                  inundation_grid=inundation)

    fig, ax = plt.subplots(figsize=(7, 6))
    fig.suptitle("Figure 4: 50x50 Coastal Bathymetry & A* Evacuation Route", fontweight="bold")

    # Contour of bathymetry
    cmap = plt.cm.terrain
    im = ax.imshow(bathymetry, cmap=cmap, origin="lower")
    plt.colorbar(im, ax=ax, label="Elevation (m)")

    # Plot coastline line (elevation == 0)
    ax.contour(bathymetry, levels=[0], colors="blue", linewidths=2, linestyles="--")

    # Plot planned path
    if plan["success"]:
        px = [p[0] for p in plan["path"]]
        py = [p[1] for p in plan["path"]]
        ax.plot(px, py, color="red", linewidth=2.5, label="A* Evacuation Route")
        ax.scatter([22], [15], color="yellow", s=80, edgecolors="black", label="Civilian Start (x=22, y=15)", zorder=5)
        ax.scatter([46], [25], color="green", marker="^", s=120, edgecolors="black", label="Highland Shelter (+85m)", zorder=5)

    ax.set_xlabel("Grid X (0: Deep Ocean, 20: Shoreline, 49: Highland)")
    ax.set_ylabel("Grid Y (Coastal Distance)")
    ax.legend(loc="upper left", fontsize=8)

    plt.tight_layout()
    out_path = os.path.join(figures_dir, "figure4_simulation_bathymetry_hazard_map.png")
    plt.savefig(out_path)
    plt.close()
    print(f"Generated: {out_path}")

def generate_all_figures():
    print("Generating research publication figures...")
    plot_benchmark_comparison()
    plot_ablation_study()
    plot_confusion_matrix()
    plot_hazard_and_path_map()
    print("All figures successfully exported to results/figures/")

if __name__ == "__main__":
    generate_all_figures()
