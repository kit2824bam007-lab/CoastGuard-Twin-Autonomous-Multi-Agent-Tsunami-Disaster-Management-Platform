"""
Backtesting platform to evaluate model prediction performance on historical events.
Saves standard evaluation metrics to docs/backtest_report.md.
"""
import os
import json
from app.services.risk_model import RuleBasedRiskModel, get_active_risk_model

HISTORICAL_CATALOG = [
    # Format: {"name": ..., "mag": ..., "depth": ..., "lat": ..., "lon": ..., "is_offshore": ..., "tsunami": ... (y)}
    {"name": "Valdivia, Chile (1960)", "mag": 9.5, "depth": 33.0, "lat": -38.2, "lon": -73.0, "is_offshore": True, "tsunami": 1},
    {"name": "Prince William Sound, Alaska (1964)", "mag": 9.2, "depth": 25.0, "lat": 61.0, "lon": -147.7, "is_offshore": True, "tsunami": 1},
    {"name": "Sumatra-Andaman (2004)", "mag": 9.1, "depth": 30.0, "lat": 3.3, "lon": 95.9, "is_offshore": True, "tsunami": 1},
    {"name": "Tohoku, Japan (2011)", "mag": 9.0, "depth": 24.0, "lat": 38.3, "lon": 142.4, "is_offshore": True, "tsunami": 1},
    {"name": "Maule, Chile (2010)", "mag": 8.8, "depth": 35.0, "lat": -35.9, "lon": -72.7, "is_offshore": True, "tsunami": 1},
    {"name": "Nias, Indonesia (2005)", "mag": 8.6, "depth": 30.0, "lat": 2.1, "lon": 97.0, "is_offshore": True, "tsunami": 1},
    {"name": "Samoa (2009)", "mag": 8.1, "depth": 18.0, "lat": -15.5, "lon": -172.0, "is_offshore": True, "tsunami": 1},
    {"name": "Fukushima, Japan (2022)", "mag": 7.4, "depth": 57.0, "lat": 37.7, "lon": 141.6, "is_offshore": True, "tsunami": 1},
    {"name": "Hokkaido, Japan (2003)", "mag": 8.3, "depth": 27.0, "lat": 41.8, "lon": 144.1, "is_offshore": True, "tsunami": 1},
    {"name": "Illapel, Chile (2015)", "mag": 8.3, "depth": 22.0, "lat": -31.6, "lon": -71.7, "is_offshore": True, "tsunami": 1},
    {"name": "Solomon Islands (2013)", "mag": 8.0, "depth": 28.0, "lat": -10.7, "lon": 165.1, "is_offshore": True, "tsunami": 1},
    {"name": "Mentawai, Indonesia (2010)", "mag": 7.8, "depth": 20.0, "lat": -3.5, "lon": 100.1, "is_offshore": True, "tsunami": 1},
    {"name": "Queen Charlotte, Canada (2012)", "mag": 7.8, "depth": 14.0, "lat": 52.8, "lon": -132.1, "is_offshore": True, "tsunami": 1},
    {"name": "Iquique, Chile (2014)", "mag": 8.2, "depth": 25.0, "lat": -19.6, "lon": -70.8, "is_offshore": True, "tsunami": 1},
    {"name": "Kaikoura, New Zealand (2016)", "mag": 7.8, "depth": 15.0, "lat": -42.7, "lon": 173.0, "is_offshore": True, "tsunami": 1},
    {"name": "Palu, Indonesia (2018)", "mag": 7.5, "depth": 20.0, "lat": -0.9, "lon": 119.8, "is_offshore": True, "tsunami": 1},
    {"name": "Kermadec Islands, NZ (2021)", "mag": 8.1, "depth": 19.0, "lat": -29.7, "lon": -177.3, "is_offshore": True, "tsunami": 1},
    {"name": "Chignik, Alaska (2021)", "mag": 8.2, "depth": 32.0, "lat": 55.4, "lon": -157.9, "is_offshore": True, "tsunami": 1},
    {"name": "Java, Indonesia (2006)", "mag": 7.7, "depth": 34.0, "lat": -9.3, "lon": 107.3, "is_offshore": True, "tsunami": 1},
    {"name": "Hualien, Taiwan (2024)", "mag": 7.4, "depth": 34.0, "lat": 23.8, "lon": 121.6, "is_offshore": True, "tsunami": 1},
    
    # Non-tsunamigenic because inland
    {"name": "Sichuan, China (2008)", "mag": 7.9, "depth": 19.0, "lat": 31.0, "lon": 103.4, "is_offshore": False, "tsunami": 0},
    {"name": "Nepal (2015)", "mag": 7.8, "depth": 15.0, "lat": 28.2, "lon": 84.7, "is_offshore": False, "tsunami": 0},
    {"name": "Kahramanmaras, Turkey (2023)", "mag": 7.8, "depth": 10.0, "lat": 37.2, "lon": 37.0, "is_offshore": False, "tsunami": 0},
    {"name": "Kobe, Japan (1995)", "mag": 6.9, "depth": 16.0, "lat": 34.6, "lon": 135.0, "is_offshore": False, "tsunami": 0},
    {"name": "Kumamoto, Japan (2016)", "mag": 7.0, "depth": 10.0, "lat": 32.8, "lon": 130.8, "is_offshore": False, "tsunami": 0},
    {"name": "Loma Prieta, USA (1989)", "mag": 6.9, "depth": 19.0, "lat": 37.0, "lon": -121.9, "is_offshore": False, "tsunami": 0},
    {"name": "Cianjur, Indonesia (2022)", "mag": 5.6, "depth": 10.0, "lat": -6.8, "lon": 107.1, "is_offshore": False, "tsunami": 0},
    {"name": "Bam, Iran (2003)", "mag": 6.6, "depth": 10.0, "lat": 29.0, "lon": 58.3, "is_offshore": False, "tsunami": 0},
    
    # Non-tsunamigenic because deep water
    {"name": "Fiji (2018)", "mag": 8.2, "depth": 563.0, "lat": -18.4, "lon": -178.1, "is_offshore": True, "tsunami": 0},
    {"name": "Sea of Okhotsk (2013)", "mag": 8.3, "depth": 609.0, "lat": 54.8, "lon": 153.2, "is_offshore": True, "tsunami": 0},
    {"name": "Mariana Islands (2016)", "mag": 7.9, "depth": 212.0, "lat": 20.8, "lon": 145.6, "is_offshore": True, "tsunami": 0},
    {"name": "Bonin Islands, Japan (2015)", "mag": 7.8, "depth": 680.0, "lat": 27.8, "lon": 140.5, "is_offshore": True, "tsunami": 0},
    
    # Non-tsunamigenic because strike-slip/minor
    {"name": "Wharton Basin (2012)", "mag": 8.6, "depth": 20.0, "lat": 2.3, "lon": 93.0, "is_offshore": True, "tsunami": 0},
    {"name": "Lombok, Indonesia (2018)", "mag": 6.9, "depth": 10.0, "lat": -8.3, "lon": 116.5, "is_offshore": True, "tsunami": 0},
    {"name": "Gulf of Alaska (2018)", "mag": 7.9, "depth": 14.0, "lat": 56.0, "lon": -149.1, "is_offshore": True, "tsunami": 0},
    {"name": "Fukushima Inland (2015)", "mag": 5.3, "depth": 40.0, "lat": 37.4, "lon": 140.9, "is_offshore": False, "tsunami": 0},
    {"name": "Tokyo Bay (2015)", "mag": 5.2, "depth": 57.0, "lat": 35.5, "lon": 139.8, "is_offshore": True, "tsunami": 0},
    {"name": "Offshore Oregon (2021)", "mag": 5.8, "depth": 10.0, "lat": 44.3, "lon": -125.0, "is_offshore": True, "tsunami": 0},
    {"name": "Java coast minor (2021)", "mag": 6.1, "depth": 80.0, "lat": -8.2, "lon": 112.5, "is_offshore": True, "tsunami": 0},
    {"name": "Christchurch, NZ (2011)", "mag": 6.2, "depth": 5.0, "lat": -43.6, "lon": 172.7, "is_offshore": False, "tsunami": 0}
]


def evaluate_model(model):
    """Evaluates the model over the catalog and compiles confusion metrics."""
    tp, fp, tn, fn = 0, 0, 0, 0
    results = []

    for item in HISTORICAL_CATALOG:
        y_true = item["tsunami"]

        res = model.predict(
            magnitude=item["mag"],
            depth_km=item["depth"],
            latitude=item["lat"],
            longitude=item["lon"],
            is_offshore=item["is_offshore"]
        )

        # Classification boundary:
        # For RuleBased: risk_level in {"HIGH", "SEVERE"} -> Positive
        # For MLRiskModel: risk_score >= 0.50 -> Positive
        if res.model_version.startswith("ml"):
            is_positive = res.risk_score >= 0.50
        else:
            is_positive = res.risk_level in ("HIGH", "SEVERE")

        y_pred = 1 if is_positive else 0

        if y_true == 1 and y_pred == 1:
            tp += 1
            status = "TP"
        elif y_true == 0 and y_pred == 1:
            fp += 1
            status = "FP"
        elif y_true == 0 and y_pred == 0:
            tn += 1
            status = "TN"
        else:
            fn += 1
            status = "FN"

        results.append({
            "name": item["name"],
            "mag": item["mag"],
            "depth": item["depth"],
            "is_offshore": item["is_offshore"],
            "y_true": y_true,
            "y_pred": y_pred,
            "score": res.risk_score,
            "level": res.risk_level,
            "status": status
        })

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    far = fp / (tn + fp) if (tn + fp) > 0 else 0
    accuracy = (tp + tn) / len(HISTORICAL_CATALOG)

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "far": far,
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "details": results
    }


def run_backtest_suite():
    """Runs backtesting for both models and writes a markdown report."""
    rule_model = RuleBasedRiskModel()
    ml_model = get_active_risk_model()

    print("Running backtest for Rule-Based model...")
    rule_metrics = evaluate_model(rule_model)

    print("Running backtest for ML model...")
    ml_metrics = evaluate_model(ml_model)

    # Format output markdown report
    output_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    docs_path = os.path.join(output_dir, "docs")
    os.makedirs(docs_path, exist_ok=True)
    report_file = os.path.join(docs_path, "backtest_report.md")

    mode_info = "ML Model (ACTIVE)" if ml_metrics["details"][0]["score"] != rule_metrics["details"][0]["score"] else "ML Model (FALLBACK - Rule Based ACTIVE)"

    md = f"""# Historical Model Validation & Backtest Report

This validation report evaluates the accuracy of the **Rule-Based Risk Model** and the **Machine Learning Risk Model** against a manually compiled catalog of **{len(HISTORICAL_CATALOG)} landmark historical earthquakes** (including 20 famous tsunamigenic and 20 non-tsunamigenic control cases).

*   **Active ML Mode during execution:** {mode_info}

---

## 1. Summary Performance Metrics

| Metric | Rule-Based Model (MVP) | Machine Learning Model (RF) | Description |
| :--- | :---: | :---: | :--- |
| **Accuracy** | {rule_metrics["accuracy"]:.2%} | {ml_metrics["accuracy"]:.2%} | Overall correct forecasts / total catalog |
| **Precision** | {rule_metrics["precision"]:.2%} | {ml_metrics["precision"]:.2%} | Fraction of issued alerts that were true tsunamis |
| **Recall (Sensitivity)** | {rule_metrics["recall"]:.2%} | {ml_metrics["recall"]:.2%} | Fraction of actual tsunamis correctly alerted |
| **F1-Score** | {rule_metrics["f1"]:.2%} | {ml_metrics["f1"]:.2%} | Harmonic mean of precision and recall |
| **False Alarm Rate (FAR)** | {rule_metrics["far"]:.2%} | {ml_metrics["far"]:.2%} | Fraction of safe events that triggered false alerts |

---

## 2. Confusion Matrices

### Rule-Based Model
*   **True Positives (TP):** {rule_metrics["tp"]}
*   **False Positives (FP):** {rule_metrics["fp"]}
*   **True Negatives (TN):** {rule_metrics["tn"]}
*   **False Negatives (FN):** {rule_metrics["fn"]}

### Machine Learning Model (RF)
*   **True Positives (TP):** {ml_metrics["tp"]}
*   **False Positives (FP):** {ml_metrics["fp"]}
*   **True Negatives (TN):** {ml_metrics["tn"]}
*   **False Negatives (FN):** {ml_metrics["fn"]}

---

## 3. Detailed Historical Catalog Run Results

Below are the individual evaluation rows for both models:

| Event Name | M | Depth (km) | Land/Sea | True | Rule Pred | ML Pred (Score) | Status (Rule/ML) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
"""

    for i in range(len(HISTORICAL_CATALOG)):
        r_item = rule_metrics["details"][i]
        m_item = ml_metrics["details"][i]
        geo = "Sea" if r_item["is_offshore"] else "Land"
        md += f"| {r_item['name']} | {r_item['mag']:.1f} | {r_item['depth']:.0f} | {geo} | **{r_item['y_true']}** | {r_item['level']} | {m_item['level']} ({m_item['score']:.2f}) | `{r_item['status']}` / `{m_item['status']}` |\n"

    with open(report_file, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"\nSuccessfully generated backtest report: {report_file}")
    print(f"ML Model F1-Score: {ml_metrics['f1']:.2%} | Rule-Based F1-Score: {rule_metrics['f1']:.2%}")


if __name__ == "__main__":
    run_backtest_suite()
