# IEEE Research Paper Manuscript: CoastGuard Twin

This directory contains the IEEE-formatted conference research paper manuscript for **CoastGuard Twin**, aligned with verified empirical benchmarks and reproducibility artifacts.

## Files
- `IEEE_CoastGuard_Twin.tex`: Complete IEEE conference LaTeX manuscript formatted under the official two-column `IEEEtran` standard.
- Figure references point to `../results/figures/`:
  - `figure1_benchmark_comparison_errorbars.png` (Benchmark error-bar comparison)
  - `figure2_ablation_component_breakdown.png` (5-variant component ablation)
  - `figure3_ml_confusion_matrix_heatmap.png` (Random Forest confusion matrix)
  - `figure4_simulation_bathymetry_hazard_map.png` (Topographic grid, tsunami surge, and $A^*$ route)

## How to Compile
You can compile this paper using standard LaTeX distributions (TeX Live, MiKTeX, MacTeX) or upload the repository to [Overleaf](https://www.overleaf.com):

```bash
cd paper
pdflatex IEEE_CoastGuard_Twin.tex
pdflatex IEEE_CoastGuard_Twin.tex
```

## Structure & Sections
1. **Title & Abstract:** Empirical problem definition and quantitative findings across $N=30$ trials.
2. **Introduction:** Near-field tsunami emergency context and explicit contributions.
3. **Related Work:** Literature grounding in TEWS, MAS, and emergency routing with verified citations.
4. **System Architecture & Problem Formulation:**
   - Topographic & bathymetric 2D grid
   - Tsunami surge equations (Abe scaling & Green's law)
   - Heterogeneous swarm dynamics & modified PSO equations
   - Hazard-aware $A^*$ cost function with elevation and depth barriers
   - Dynamic civilian evacuation model
5. **Experimental Evaluation & Results:**
   - Multi-trial paired benchmark results ($N=30$, with 95% CIs and $p$-values)
   - Component ablation analysis ($N=15$ trials per variant)
   - Machine learning evaluation (synthetic threshold disclosure & historical backtesting)
6. **Discussion & Limitations:** Threats to validity, physical model approximations, single points of failure.
7. **Conclusion & Future Work:** Summary and roadmaps to 2D shallow-water PDE hydrodynamic models and physical testbeds.
8. **References:** Verified IEEE citations.
