"""
Physical wave modeling service.
Approximates travel time and coastline wave heights using linear shallow water equations
and Green's Law coastal amplification.
"""
from app.services.geo_utils import haversine_distance

# Selected key global coastal responder stations
COASTAL_STATIONS = [
    {"name": "Tokyo, Japan", "lat": 35.6762, "lon": 139.6503},
    {"name": "Banda Aceh, Indonesia", "lat": 5.5483, "lon": 95.3238},
    {"name": "Hilo, Hawaii, USA", "lat": 19.7241, "lon": -155.0868},
    {"name": "Valparaiso, Chile", "lat": -33.0472, "lon": -71.6127},
    {"name": "Crescent City, California, USA", "lat": 41.7558, "lon": -124.2026},
    {"name": "Sydney, Australia", "lat": -33.8688, "lon": 151.2093},
    {"name": "San Francisco, USA", "lat": 37.7749, "lon": -122.4194},
    {"name": "Rakata Island, Indonesia", "lat": -6.155, "lon": 105.427} # field validation site
]

# Shallow water wave propagation parameters
OCEAN_DEPTH_M = 4000.0        # Average deep ocean depth
COASTAL_DEPTH_M = 8.0         # Coastal harbor shelf depth
GRAVITY = 9.81                # m/s^2

# Deep ocean wave speed: v = sqrt(g * h)
WAVE_SPEED_M_S = (GRAVITY * OCEAN_DEPTH_M) ** 0.5
WAVE_SPEED_KM_H = WAVE_SPEED_M_S * 3.6  # approx 713 km/h


def predict_wave_metrics(
    station_lat: float,
    station_lon: float,
    eq_lat: float,
    eq_lon: float,
    magnitude: float,
    depth_km: float,
    is_offshore: bool
) -> tuple[float, float, float]:
    """
    Computes distance, travel time, and coastal wave height for a specific station.
    Returns: (distance_km, travel_time_hours, wave_height_meters)
    """
    # 1. Geodesic Distance
    dist_km = haversine_distance(eq_lat, eq_lon, station_lat, station_lon)

    # If the quake is inland or magnitude is below 6.0, no wave is generated
    if not is_offshore or magnitude < 6.0:
        return dist_km, 0.0, 0.0

    # 2. Arrival Time
    travel_time_hours = dist_km / WAVE_SPEED_KM_H

    # 3. Wave Height Modeling
    # Tsunami initial vertical water displacement at source:
    # A simple empirical scaling: H0 ~ 10^(0.52 * M - 3.4) meters (Abe's formula scaling)
    # Further damp and attenuate height based on earthquake deepness
    import math
    h0 = 10 ** (0.52 * magnitude - 3.4)
    depth_damping = math.exp(-depth_km / 50.0)  # deeper quakes reduce vertical coupling
    initial_wave_height = h0 * depth_damping

    # Green's Law coastal amplification: H_coast = H_deep * (h_deep / h_coast) ^ 0.25
    amplification_factor = (OCEAN_DEPTH_M / COASTAL_DEPTH_M) ** 0.25  # approx 4.73

    # Cylindrical wave energy dispersion / radial attenuation over distance d (km)
    dispersion_factor = math.exp(-dist_km / 3500.0)

    wave_height_coast = initial_wave_height * amplification_factor * dispersion_factor

    # Add realistic bounds (a major Tohoku-scale tsunami might yield 15-30m coastal surges)
    wave_height_coast = min(35.0, max(0.0, wave_height_coast))

    return round(dist_km, 1), round(travel_time_hours, 2), round(wave_height_coast, 2)


def generate_tsunami_forecasts(
    eq_lat: float,
    eq_lon: float,
    magnitude: float,
    depth_km: float,
    is_offshore: bool
) -> list[dict]:
    """
    Generates a list of forecasts for all coastal stations.
    """
    forecasts = []
    # Only forecast if the quake is offshore and strong enough, to avoid clutter
    if not is_offshore or magnitude < 6.0:
        return forecasts

    for station in COASTAL_STATIONS:
        dist, arrival, height = predict_wave_metrics(
            station["lat"], station["lon"],
            eq_lat, eq_lon,
            magnitude, depth_km, is_offshore
        )
        # Skip location if wave height is completely negligible (< 0.01m) and distance is huge
        if height < 0.01 and dist > 10000:
            continue

        forecasts.append({
            "station_name": station["name"],
            "distance_km": dist,
            "arrival_time_hours": arrival,
            "wave_height_m": height
        })

    # Sort by arrival time
    forecasts.sort(key=lambda x: x["arrival_time_hours"])
    return forecasts
