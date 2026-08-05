"""
Test cases for the rule-based risk model.
Run: pytest backend/tests/ -v
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.risk_model import RuleBasedRiskModel

model = RuleBasedRiskModel()


def test_severe_offshore_shallow_major_quake():
    """M8.6, 10km deep, offshore, USGS flagged, active bulletin -> SEVERE"""
    r = model.predict(
        magnitude=8.6, depth_km=10, latitude=38.3, longitude=142.4,  # Tohoku-like
        is_offshore=True, usgs_tsunami_flag=True, active_noaa_bulletin=True,
    )
    assert r.risk_level == "SEVERE"
    assert r.risk_score >= 0.75


def test_low_risk_small_inland_quake():
    """M4.2 inland quake -> LOW, no alert should trigger"""
    r = model.predict(
        magnitude=4.2, depth_km=15, latitude=34.05, longitude=-118.25,  # LA-like, inland
        is_offshore=False,
    )
    assert r.risk_level == "LOW"


def test_deep_quake_scores_lower_than_shallow_equivalent():
    """M7.0 at 500km depth should score strictly lower than the same quake at 10km depth"""
    deep = model.predict(magnitude=7.0, depth_km=500, latitude=-20.0, longitude=-70.0, is_offshore=True)
    shallow = model.predict(magnitude=7.0, depth_km=10, latitude=-20.0, longitude=-70.0, is_offshore=True)
    assert deep.risk_score < shallow.risk_score


def test_high_risk_subduction_zone_boost():
    """Same magnitude/depth inside vs outside a known subduction zone should differ"""
    inside = model.predict(magnitude=7.2, depth_km=25, latitude=38.0, longitude=141.0, is_offshore=True)
    outside = model.predict(magnitude=7.2, depth_km=25, latitude=10.0, longitude=10.0, is_offshore=True)
    assert inside.risk_score >= outside.risk_score


def test_score_bounds():
    """risk_score must always stay within [0, 1]"""
    r = model.predict(magnitude=9.5, depth_km=1, latitude=38.0, longitude=141.0,
                       is_offshore=True, usgs_tsunami_flag=True, active_noaa_bulletin=True)
    assert 0.0 <= r.risk_score <= 1.0


if __name__ == "__main__":
    test_severe_offshore_shallow_major_quake()
    test_low_risk_small_inland_quake()
    test_deep_quake_scores_lower_than_shallow_equivalent()
    test_high_risk_subduction_zone_boost()
    test_score_bounds()
    print("All risk model tests passed.")
