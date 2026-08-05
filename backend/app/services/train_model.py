"""
Training script for the Tsunami ML Risk prediction model.
"""
import os
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score


def generate_historical_dataset(seed=42):
    """
    Generates a high-quality historical dataset of earthquakes with tsunami labels.
    Uses realistic distribution rules to model the physical tsunamigenesis relations.
    """
    np.random.seed(seed)
    n_samples = 800

    # Features: [magnitude, depth_km, latitude, longitude, is_offshore]
    # Label: tsunami_generated (0 or 1)
    X = []
    y = []

    for _ in range(n_samples):
        # Determine if offshore (roughly 70% of earthquakes globally are offshore/coastal)
        is_offshore = 1 if np.random.rand() < 0.7 else 0

        # Magnitude (log-linear Richter distribution)
        # We focus on M5.0 to M9.5
        magnitude = np.random.uniform(5.0, 9.5)

        # Depth (shallow 0-70km, intermediate 70-300km, deep 300-700km)
        depth_dist = np.random.rand()
        if depth_dist < 0.70:
            depth_km = np.random.uniform(5, 70)  # shallow rupture
        elif depth_dist < 0.90:
            depth_km = np.random.uniform(70, 300) # intermediate
        else:
            depth_km = np.random.uniform(300, 700) # deep

        # Random global coordinates
        latitude = np.random.uniform(-70.0, 70.0)
        longitude = np.random.uniform(-180.0, 180.0)

        # Determine class: Tsunami generated?
        # Physical rules:
        # 1. Tsunami requires offshore epicenter
        # 2. Tsunami is extremely rare below magnitude 6.5
        # 3. Tsunami requires shallow coupling (depth < 80km, preferably < 35km)
        # 4. Proximity to subduction zones (Pacific Ring of Fire, Sunda Trench, etc. boosts probability)
        # Let's write a probability function and threshold it
        prob = 0.0

        if is_offshore == 1:
            if magnitude >= 8.2:
                prob = 0.92
            elif magnitude >= 7.5:
                prob = 0.65
            elif magnitude >= 6.8:
                prob = 0.30
            elif magnitude >= 6.2:
                prob = 0.10
            else:
                prob = 0.01

            # Damping due to depth
            if depth_km > 100:
                prob *= 0.01
            elif depth_km > 50:
                prob *= 0.2
            elif depth_km > 30:
                prob *= 0.7

            # Boost if in a high-risk zone (Ring of fire/trenches)
            # Rough lat/lon check
            in_fire_ring = (120 <= longitude <= 180 or -180 <= longitude <= -60) and (-60 <= latitude <= 60)
            in_sunda = (90 <= longitude <= 100) and (-10 <= latitude <= 15)
            if in_fire_ring or in_sunda:
                prob = min(0.99, prob * 1.3)
        else:
            # Inland quakes
            prob = 0.0

        # Small random noise (5% chance of anomalies, e.g. inland lake slide, sub-sea landslides)
        if np.random.rand() < 0.05:
            # Random flip
            label = 1 if np.random.rand() < 0.1 else 0
        else:
            label = 1 if np.random.rand() < prob else 0

        X.append([magnitude, depth_km, latitude, longitude, is_offshore])
        y.append(label)

    # Inject real famous historical events to ensure their training representation
    # Format: [M, depth, lat, lon, is_offshore] -> label
    famous_events = [
        ([9.1, 24.0, 38.3, 142.4, 1], 1),    # Tohoku 2011
        ([9.1, 30.0, 3.3, 95.9, 1], 1),      # Sumatra 2004
        ([8.8, 35.0, -35.9, -72.7, 1], 1),   # Chile 2010
        ([7.9, 19.0, 31.0, 103.4, 0], 0),    # Sichuan 2008 (inland)
        ([7.8, 15.0, 28.2, 84.7, 0], 0),     # Nepal 2015 (inland)
        ([8.2, 563.0, -18.4, -178.1, 1], 0), # Fiji 2018 (deep sea, but 560km deep -> no tsunami)
        ([8.3, 609.0, 54.8, 153.2, 1], 0),   # Sea of Okhotsk 2013 (600km deep -> no tsunami)
        ([7.5, 210.0, 36.5, 70.3, 0], 0),    # Hindu Kush 2015 (deep/inland)
        ([6.1, 10.0, -8.3, 116.1, 1], 0),    # Lombok 2018 (too small/offshore -> no tsunami)
    ]
    for features, label in famous_events:
        X.append(features)
        y.append(label)

    return np.array(X), np.array(y)


def train_and_save_model():
    """Trains the RandomForest Classifier and exports model.pkl."""
    print("Generating simulated and real-world historical dataset...")
    X, y = generate_historical_dataset()

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

    print(f"Dataset Size: {len(X)} events (Tsunamigenic: {sum(y)}, Safe: {len(y) - sum(y)})")
    print("Fitting RandomForestClassifier...")

    clf = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)
    clf.fit(X_train, y_train)

    # Evaluate
    y_pred = clf.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"\nModel Test Accuracy: {accuracy:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=["No Tsunami", "Tsunami Generated"]))

    # Save to file
    out_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    model_path = os.path.join(out_dir, "model.pkl")

    joblib.dump(clf, model_path)
    print(f"Successfully saved trained model to {model_path}")


if __name__ == "__main__":
    train_and_save_model()
