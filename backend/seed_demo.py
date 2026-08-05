"""
Demo Seed Script & End-to-End Test Trigger
"""
import sys
import time
import requests

BASE_URL = "http://localhost:8000"

def run_demo():
    print("=========================================================")
    print(" CoastGuard Twin — End-to-End Simulation Demo Script")
    print("=========================================================")
    
    try:
        # 1. Health check
        res = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"[1] Backend Health: {res.json()}")

        # 2. Reset simulation
        res = requests.post(f"{BASE_URL}/api/sensors/reset", timeout=5)
        print(f"[2] Reset Simulation: {res.json()['message']}")
        time.sleep(1)

        # 3. Trigger Earthquake Event
        print("\n[3] Injecting Earthquake Event (Magnitude 7.8, Distance 45km)...")
        res = requests.post(
            f"{BASE_URL}/api/sensors/trigger-event",
            json={"magnitude": 7.8, "distance_km": 45.0},
            timeout=5
        )
        print(f" -> Event Triggered: {res.json()['status']}")
        time.sleep(2)

        # 4. Fetch Digital Twin state
        res = requests.get(f"{BASE_URL}/api/twin/state", timeout=5)
        twin_data = res.json()
        print(f"\n[4] Layer 2 Digital Twin Fused State:")
        print(f" -> Max Inundation Depth: {twin_data['summary']['max_inundation_depth_m']}m")
        print(f" -> High Risk Cells: {twin_data['summary']['high_risk_cells_count']}")

        # 5. Fetch Swarm Mesh Topology
        res = requests.get(f"{BASE_URL}/api/swarm/topology", timeout=5)
        swarm_data = res.json()
        print(f"\n[5] Layer 3 Swarm Intelligence:")
        print(f" -> Active Agents: {swarm_data['total_active']}")
        print(f" -> Mesh Edges: {len(swarm_data['edges'])}")

        # 6. Simulate agent loss
        print("\n[6] Simulating UAV Agent Loss (UAV-101)...")
        res = requests.post(f"{BASE_URL}/api/swarm/simulate-loss", json={"agent_id": "UAV-101"}, timeout=5)
        print(f" -> {res.json()['message']}")

        # 7. Check Hazard Severity Classification
        res = requests.get(f"{BASE_URL}/api/alerts/severity", timeout=5)
        sev_data = res.json()
        print(f"\n[7] Layer 5 Hazard Severity Classification:")
        print(f" -> Predicted Class: {sev_data['classification']['predicted_class']}")
        print(f" -> Confidence: {sev_data['classification']['confidence'] * 100}%")

        # 8. Check Metrics & Benchmark
        res = requests.get(f"{BASE_URL}/api/metrics/benchmark", timeout=5)
        bench = res.json()
        print(f"\n[8] Comparative Metrics Dashboard (Baseline vs Proposed Swarm):")
        for m in bench['metrics']:
            print(f" -> {m['title']}: Baseline = {m['baseline']}{m['unit']}, Proposed = {m['proposed_swarm']}{m['unit']} (Improvement: {m['improvement_percentage']}%)")

        print("\n=========================================================")
        print(" Demo Walkthrough Completed Successfully!")
        print("=========================================================")

    except Exception as e:
        print(f"Error running demo seed script: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_demo()
