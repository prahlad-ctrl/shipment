"""
Geocoding and distance utilities for shipment route calculations.
Uses the Haversine formula for great-circle distances and provides
coordinate lookups for major logistics hubs worldwide.
"""

import math
import json
import os
import os
import urllib.request
import urllib.parse
from typing import Tuple, List, Dict, Optional
import searoute as sr

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

# Cache for loaded port data
_ports_cache: Optional[Dict] = None


def _load_ports() -> Dict:
    """Load ports data from JSON file with caching."""
    global _ports_cache
    if _ports_cache is None:
        with open(os.path.join(DATA_DIR, "ports.json"), "r") as f:
            _ports_cache = json.load(f)
    return _ports_cache

_coord_cache = {}

def get_coordinates(location: str) -> Optional[Tuple[float, float]]:
    """
    Get (lat, lng) coordinates for a known logistics hub.
    Returns None if the location is not found.
    """
    if location in _coord_cache:
        return _coord_cache[location]
    ports = _load_ports()
    normalized = location.lower().replace(" ", "_").replace("-", "_")

    # Direct match
    if normalized in ports:
        port = ports[normalized]
        return (port["lat"], port["lng"])

    # Fuzzy match on name or code
    for key, port in ports.items():
        if (normalized in key or
            normalized in port["name"].lower() or
            normalized == port["code"].lower() or
            normalized in port.get("nearby_airport", "").lower()):
            return (port["lat"], port["lng"])

    # Fallback to Nominatim geocoding API for arbitrary locations
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(location)}&format=json&limit=1"
        req = urllib.request.Request(url, headers={'User-Agent': 'ShipmentAgent/1.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            if data and len(data) > 0:
                lat = float(data[0]["lat"])
                lon = float(data[0]["lon"])
                _coord_cache[location] = (lat, lon)
                return (lat, lon)
    except Exception as e:
        print(f"Geocoding fallback failed for {location}: {e}")

    return None

def is_land_connected(origin: str, destination: str) -> bool:
    """
    Check if two locations are connected by road using the public OSRM API.
    A successful driving route indicates they are on the same landmass 
    (or connected by ferry/tunnel) allowing road and rail freight.
    """
    origin_coords = get_coordinates(origin)
    dest_coords = get_coordinates(destination)
    if origin_coords is None or dest_coords is None:
        return False
        
    try:
        url = f"http://router.project-osrm.org/route/v1/driving/{origin_coords[1]},{origin_coords[0]};{dest_coords[1]},{dest_coords[0]}?overview=false"
        req = urllib.request.Request(url, headers={'User-Agent': 'ShipmentAgent/1.0'})
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode())
            if data.get("code") == "Ok":
                return True
    except Exception as e:
        print(f"OSRM connectivity check failed: {e}")
        # If API fails or times out, fallback to returning True since we don't want to break the whole application.
        dist = calculate_distance(origin, destination)
        return dist is not None and dist < 5000
    return False


def haversine_distance(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """
    Calculate the great-circle distance in kilometers between two points
    using the Haversine formula.
    """
    R = 6371  # Earth's radius in kilometers

    lat1_r, lat2_r = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (math.sin(dlat / 2) ** 2 +
         math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def calculate_distance(origin: str, destination: str) -> Optional[float]:
    """
    Calculate distance in km between two named locations.
    Returns None if either location is not found.
    """
    origin_coords = get_coordinates(origin)
    dest_coords = get_coordinates(destination)

    if origin_coords is None or dest_coords is None:
        return None

    return haversine_distance(
        origin_coords[0], origin_coords[1],
        dest_coords[0], dest_coords[1]
    )


def generate_waypoints(
    origin: Tuple[float, float],
    destination: Tuple[float, float],
    num_points: int = 20
) -> List[Tuple[float, float]]:
    """
    Generate intermediate waypoints along a great-circle path
    for map visualization.
    """
    lat1, lon1 = math.radians(origin[0]), math.radians(origin[1])
    lat2, lon2 = math.radians(destination[0]), math.radians(destination[1])

    d = haversine_distance(origin[0], origin[1], destination[0], destination[1])
    if d == 0:
        return [origin, destination]
    d_rad = d / 6371  # angular distance in radians

    waypoints = []
    for i in range(num_points + 1):
        f = i / num_points
        a = math.sin((1 - f) * d_rad) / math.sin(d_rad) if d_rad > 0 else 1 - f
        b = math.sin(f * d_rad) / math.sin(d_rad) if d_rad > 0 else f

        x = a * math.cos(lat1) * math.cos(lon1) + b * math.cos(lat2) * math.cos(lon2)
        y = a * math.cos(lat1) * math.sin(lon1) + b * math.cos(lat2) * math.sin(lon2)
        z = a * math.sin(lat1) + b * math.sin(lat2)

        lat = math.degrees(math.atan2(z, math.sqrt(x ** 2 + y ** 2)))
        lon = math.degrees(math.atan2(y, x))
        waypoints.append((round(lat, 4), round(lon, 4)))

    return waypoints


def generate_mode_waypoints(
    origin: Tuple[float, float],
    destination: Tuple[float, float],
    mode: str
) -> List[Tuple[float, float]]:
    """
    Generate high-fidelity waypoints based on transport mode.
    Falls back to great-circle generation if third-party APIs fail.
    """
    try:
        if mode == "sea":
            # searoute expects [longitude, latitude]
            route = sr.searoute([origin[1], origin[0]], [destination[1], destination[0]], append_orig_dest=True)
            if route and "geometry" in route and "coordinates" in route["geometry"]:
                # return [lat, lng]
                return [(float(c[1]), float(c[0])) for c in route["geometry"]["coordinates"]]
                
        elif mode == "road":
            # OSRM expects lon,lat
            url = f"http://router.project-osrm.org/route/v1/driving/{origin[1]},{origin[0]};{destination[1]},{destination[0]}?overview=full&geometries=geojson"
            req = urllib.request.Request(url, headers={'User-Agent': 'ShipmentAgent/1.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                if data.get("code") == "Ok" and data.get("routes"):
                    coords = data["routes"][0]["geometry"]["coordinates"]
                    return [(float(c[1]), float(c[0])) for c in coords]
    except Exception as e:
        print(f"High-fidelity routing failed for mode {mode}, falling back to great-circle. Error: {e}")

    # Fallback to great-circle for air or if API calls fail
    return generate_waypoints(origin, destination)


def get_route_waypoints(origin: str, destination: str, mode: str = "air") -> List[Tuple[float, float]]:
    """Generate map waypoints between two named locations considering the transport mode."""
    origin_coords = get_coordinates(origin)
    dest_coords = get_coordinates(destination)

    if origin_coords is None or dest_coords is None:
        return []

    return generate_mode_waypoints(origin_coords, dest_coords, mode)


def find_matching_location(query: str) -> Optional[str]:
    """
    Find the best matching port/hub key for a location query.
    Returns the key used in ports.json, or None.
    """
    ports = _load_ports()
    query_lower = query.lower().strip()

    # Direct key match
    normalized = query_lower.replace(" ", "_").replace("-", "_")
    if normalized in ports:
        return normalized

    # Check if query appears in port name, code, or country
    best_match = None
    for key, port in ports.items():
        name_lower = port["name"].lower()
        country_lower = port["country"].lower()
        if (query_lower in key or
            query_lower in name_lower or
            query_lower == port["code"].lower() or
            query_lower == country_lower):
            best_match = key
            # Prefer exact key or name match
            if query_lower == key or query_lower in name_lower.split(",")[0].lower():
                return key

    return best_match
