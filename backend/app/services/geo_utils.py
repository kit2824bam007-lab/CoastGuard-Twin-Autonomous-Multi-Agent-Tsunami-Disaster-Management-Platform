"""
Geographic utilities for land-sea checking and coastline distance.
Provides high-performance pure-Python point-in-polygon (PIP) checks
on simplified global continental boundaries.
"""
import math

# Representative simplified polygons for major land masses (Eurasia, Africa, Americas, Australia, Antarctica, Greenland)
# Format: list of (lon, lat) vertices. First and last vertices don't need to be identical.
CONTINENTS = {
    "Eurasia": [
        (-10.0, 36.0), (2.0, 51.0), (5.0, 60.0), (10.0, 62.0), (25.0, 71.0),
        (60.0, 73.0), (100.0, 78.0), (170.0, 70.0), (180.0, 65.0), (190.0, 65.0), # wrap eastward
        (170.0, 60.0), (140.0, 45.0), (120.0, 25.0), (108.0, 13.0), (100.0, 1.0),
        (80.0, 6.0), (70.0, 20.0), (45.0, 12.0), (35.0, 30.0), (26.0, 40.0)
    ],
    "Africa": [
        (-17.0, 15.0), (-5.0, 35.0), (10.0, 37.0), (30.0, 31.0), (32.0, 30.0),
        (43.0, 12.0), (51.0, 11.0), (40.0, -5.0), (33.0, -34.0), (18.0, -34.0),
        (10.0, -5.0), (8.0, 4.0), (-14.0, 4.0)
    ],
    "North_America": [
        (-168.0, 65.0), (-150.0, 70.0), (-120.0, 75.0), (-80.0, 82.0), (-60.0, 82.0),
        (-50.0, 50.0), (-60.0, 45.0), (-80.0, 25.0), (-80.0, 9.0), (-90.0, 15.0),
        (-105.0, 20.0), (-120.0, 30.0), (-125.0, 48.0), (-140.0, 58.0), (-160.0, 55.0)
    ],
    "South_America": [
        (-80.0, 9.0), (-70.0, 12.0), (-60.0, 10.0), (-35.0, -5.0), (-35.0, -8.0),
        (-40.0, -22.0), (-60.0, -38.0), (-65.0, -55.0), (-75.0, -55.0), (-75.0, -40.0),
        (-72.0, -20.0), (-80.0, -5.0), (-81.0, -4.0)
    ],
    "Australia": [
        (113.0, -26.0), (115.0, -35.0), (130.0, -32.0), (145.0, -38.0), (150.0, -33.0),
        (152.0, -22.0), (142.0, -10.0), (130.0, -12.0), (122.0, -16.0)
    ],
    "Antarctica": [
        (-180.0, -60.0), (180.0, -60.0), (180.0, -85.0), (-180.0, -85.0)
    ],
    "Greenland": [
        (-60.0, 60.0), (-50.0, 60.0), (-60.0, 75.0), (-40.0, 82.0), (-20.0, 70.0),
        (-40.0, 60.0)
    ],
    "India_Subcontinent": [
        (68.0, 24.0), (78.0, 35.0), (97.0, 28.0), (92.0, 21.0), (80.0, 6.0), (73.0, 8.0)
    ],
    "Madagascar": [
        (43.0, -25.0), (47.0, -25.0), (51.0, -16.0), (49.0, -12.0), (44.0, -13.0)
    ]
}


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points in kilometers."""
    R = 6371.0  # Earth's radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (math.sin(dphi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def point_in_polygon(lon: float, lat: float, polygon: list[tuple[float, float]]) -> bool:
    """Ray-casting point-in-polygon algorithm."""
    n = len(polygon)
    inside = False
    p1x, p1y = polygon[0]
    for i in range(n + 1):
        p2x, p2y = polygon[i % n]
        if lat > min(p1y, p2y):
            if lat <= max(p1y, p2y):
                if lon <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (lat - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or lon <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside


def is_on_land(lon: float, lat: float) -> bool:
    """Determine if a coordinate is on land by checking against simplified continental boundaries."""
    # Normalize longitude to [-180, 180]
    lon = ((lon + 180) % 360) - 180
    for name, poly in CONTINENTS.items():
        if point_in_polygon(lon, lat, poly):
            return True
    return False


def get_closest_point_on_segment(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> tuple[float, float]:
    """Find the closest point on the segment AB to point P in degree space."""
    ab_x = bx - ax
    ab_y = by - ay
    ap_x = px - ax
    ap_y = py - ay

    ab2 = ab_x * ab_x + ab_y * ab_y
    if ab2 == 0:
        return ax, ay

    t = (ap_x * ab_x + ap_y * ab_y) / ab2
    t = max(0.0, min(1.0, t))  # clamp to segment bounds

    return ax + t * ab_x, ay + t * ab_y


def distance_to_coastline(lon: float, lat: float) -> float:
    """Calculate the shortest distance from an earthquake epicenter to the nearest continental coastline in km."""
    # If the point is on land, the distance is 0 km (or negative, but 0 is standard)
    if is_on_land(lon, lat):
        return 0.0

    min_dist = float('inf')
    lon = ((lon + 180) % 360) - 180

    for name, poly in CONTINENTS.items():
        n = len(poly)
        for i in range(n):
            ax, ay = poly[i]
            bx, by = poly[(i + 1) % n]

            # Find the closest point in degree space
            c_lon, c_lat = get_closest_point_on_segment(lon, lat, ax, ay, bx, by)

            # Compute Haversine distance from target to this segment point
            dist = haversine_distance(lat, lon, c_lat, c_lon)
            if dist < min_dist:
                min_dist = dist

    return min_dist


def is_offshore_coordinate(lon: float, lat: float, coast_threshold_km: float = 15.0) -> bool:
    """
    Check if a coordinate points to the ocean (offshore).
    True if outside all landmasses by more than the tolerance threshold (in km).
    """
    if is_on_land(lon, lat):
        return False
    return distance_to_coastline(lon, lat) >= coast_threshold_km
