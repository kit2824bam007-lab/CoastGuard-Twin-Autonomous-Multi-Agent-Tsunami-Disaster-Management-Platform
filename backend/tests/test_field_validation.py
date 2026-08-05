"""
Field validation test simulating a deployment at Rakata Island in the Sunda Arc.
"""
import pytest
from datetime import datetime, timezone
from app.services.geo_utils import is_offshore_coordinate, distance_to_coastline
from app.services.tectonic_plates import distance_to_subduction_zone, in_subduction_zone
from app.services.wave_model import predict_wave_metrics, generate_tsunami_forecasts


def test_rakata_island_geographic_checks():
    """
    Test that spatial checks correctly identify offshore status and plate boundary closeness
    for a simulated Sunda Trench rupture.
    """
    # Sunda Trench epicenter near Rakata: -6.5 lat, 105.0 lon
    eq_lat, eq_lon = -6.5, 105.0

    # 1. Verify offshore detection (it is located in Sunda Strait ocean)
    is_off = is_offshore_coordinate(eq_lon, eq_lat)
    assert is_off is True

    dist_coast = distance_to_coastline(eq_lon, eq_lat)
    assert dist_coast > 0.0

    # 2. Verify subduction trench proximity (Sunda Trench boundary)
    zone, dist_trench = distance_to_subduction_zone(eq_lon, eq_lat)
    assert zone == "Sunda Trench"
    assert dist_trench <= 100.0  # within 100km of the plate boundary
    assert in_subduction_zone(eq_lon, eq_lat, threshold_km=150.0) is True


def test_rakata_island_wave_transit():
    """Matches the physical model parameters to confirm wave travel metrics."""
    # Rakata Island station: -6.155 lat, 105.427 lon
    rakata_lat, rakata_lon = -6.155, 105.427

    # Rupture epicenter: -6.5 lat, 105.0 lon (distance is ~60 km)
    eq_lat, eq_lon = -6.5, 105.0

    # A major M7.8 offshore shallow quake
    dist_km, travel_time_hours, wave_height_m = predict_wave_metrics(
        rakata_lat, rakata_lon,
        eq_lat, eq_lon,
        magnitude=7.8,
        depth_km=15.0,
        is_offshore=True
    )

    # Assertions
    assert 40.0 <= dist_km <= 80.0
    # Travel time for 60km at 713km/h is around 0.08 hours (~5 minutes) Succinct warning loop!
    assert 0.05 <= travel_time_hours <= 0.15
    # Wave height at Rakata coast should be substantial for M7.8 shallow event
    assert wave_height_m >= 1.0


def test_forecast_list_structure():
    """Validates the structure returned by wave forecast generation."""
    forecasts = generate_tsunami_forecasts(
        eq_lat=-6.5, eq_lon=105.0,
        magnitude=8.0, depth_km=10.0, is_offshore=True
    )
    # Validate Rakata Island is present in the list
    rakata_forecast = [f for f in forecasts if f["station_name"].startswith("Rakata")]
    assert len(rakata_forecast) == 1
    assert rakata_forecast[0]["wave_height_m"] > 0.0
    assert rakata_forecast[0]["arrival_time_hours"] > 0.0
