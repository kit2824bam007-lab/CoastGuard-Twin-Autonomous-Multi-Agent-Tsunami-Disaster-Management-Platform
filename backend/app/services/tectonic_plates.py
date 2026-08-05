"""
Tectonic plate boundary service.
Provides accurate spatial calculations to determine proximity to global subduction zones.
"""
from app.services.geo_utils import haversine_distance, get_closest_point_on_segment

# Historical high-risk subduction zone polylines
SUBDUCTION_ZONES = {
    "Sunda Trench": [
        (95.3, 5.5), (96.5, 3.0), (98.0, 1.0), (100.0, -2.0), (102.0, -5.0),
        (105.0, -7.0), (110.0, -9.0), (115.0, -10.0), (120.0, -11.0)
    ],
    "Japan/Kuril Trench": [
        (140.0, 34.0), (142.5, 36.5), (144.0, 40.0), (146.0, 43.0), (150.0, 47.0),
        (155.0, 51.0), (160.0, 54.0)
    ],
    "Mariana Trench": [
        (142.0, 22.0), (145.0, 18.0), (147.0, 14.0), (146.0, 11.0), (143.0, 10.0)
    ],
    "Cascadia Subduction Zone": [
        (-124.5, 40.0), (-124.8, 42.0), (-125.0, 45.0), (-125.5, 48.0), (-128.0, 50.0)
    ],
    "Aleutian Trench": [
        (165.0, 51.0), (175.0, 50.0), (-175.0, 51.0), (-165.0, 53.0),
        (-155.0, 55.0), (-145.0, 57.0), (-140.0, 59.0)
    ],
    "Peru-Chile Trench": [
        (-78.0, 8.0), (-81.0, -2.0), (-81.5, -5.0), (-79.0, -12.0), (-74.0, -20.0),
        (-72.0, -30.0), (-74.0, -40.0), (-75.0, -46.0)
    ],
    "Puerto Rico Trench": [
        (-68.0, 19.5), (-65.0, 19.5), (-61.0, 18.0), (-59.5, 15.0), (-59.0, 12.0)
    ]
}


def distance_to_subduction_zone(lon: float, lat: float) -> tuple[str, float]:
    """
    Calculate the shortest distance of coordinates to any known subduction zone in km.
    Returns: (subduction_zone_name, distance_km)
    """
    min_dist = float('inf')
    closest_zone = "Unknown"
    lon = ((lon + 180) % 360) - 180

    for name, polyline in SUBDUCTION_ZONES.items():
        n = len(polyline)
        for i in range(n - 1):
            ax, ay = polyline[i]
            bx, by = polyline[i + 1]

            # Find closest point on line segment
            c_lon, c_lat = get_closest_point_on_segment(lon, lat, ax, ay, bx, by)

            # Compute Haversine distance
            dist = haversine_distance(lat, lon, c_lat, c_lon)
            if dist < min_dist:
                min_dist = dist
                closest_zone = name

    return closest_zone, min_dist


def in_subduction_zone(lon: float, lat: float, threshold_km: float = 150.0) -> bool:
    """
    Check if a coordinate lies within a target threshold distance from a subduction boundary.
    """
    _, dist = distance_to_subduction_zone(lon, lat)
    return dist <= threshold_km
