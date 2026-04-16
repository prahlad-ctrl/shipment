"""
Hub Resolver Agent Node.
Resolves any origin/destination city to coordinates and maps it
to the nearest known major logistics hub from ports.json.
Uses LLM for unknown locations with algorithmic fallback.
"""

import json
import re
from typing import Dict, Any, Optional, Tuple
from agent.state import ShipmentState
from tools.geo_utils import (
    get_coordinates,
    find_matching_location,
    haversine_distance,
    _load_ports
)


# ── Known city coordinates fallback ─────────────────────────────────────────
# Covers common cities that might not be in ports.json
CITY_COORDINATES = {
    "austin": (30.2672, -97.7431),
    "dallas": (32.7767, -96.7970),
    "houston": (29.7604, -95.3698),
    "chicago": (41.8781, -87.6298),
    "san_francisco": (37.7749, -122.4194),
    "seattle": (47.6062, -122.3321),
    "miami": (25.7617, -80.1918),
    "atlanta": (33.7490, -84.3880),
    "delhi": (28.6139, 77.2090),
    "new_delhi": (28.6139, 77.2090),
    "chennai": (13.0827, 80.2707),
    "kolkata": (22.5726, 88.3639),
    "bangalore": (12.9716, 77.5946),
    "bengaluru": (12.9716, 77.5946),
    "beijing": (39.9042, 116.4074),
    "shenzhen": (22.5431, 114.0579),
    "guangzhou": (23.1291, 113.2644),
    "bangkok": (13.7563, 100.5018),
    "ho_chi_minh": (10.8231, 106.6297),
    "jakarta": (6.2088, 106.8456),
    "kuala_lumpur": (3.1390, 101.6869),
    "manila": (14.5995, 120.9842),
    "cairo": (30.0444, 31.2357),
    "lagos": (6.5244, 3.3792),
    "nairobi": (1.2921, 36.8219),
    "cape_town": (-33.9249, 18.4241),
    "johannesburg": (-26.2041, 28.0473),
    "sao_paulo": (-23.5505, -46.6333),
    "buenos_aires": (-34.6037, -58.3816),
    "mexico_city": (19.4326, -99.1332),
    "paris": (48.8566, 2.3522),
    "berlin": (52.5200, 13.4050),
    "madrid": (40.4168, -3.7038),
    "rome": (41.9028, 12.4964),
    "amsterdam": (52.3676, 4.9041),
    "zurich": (47.3769, 8.5417),
    "moscow": (55.7558, 37.6173),
    "doha": (25.2854, 51.5310),
    "riyadh": (24.7136, 46.6753),
    "abu_dhabi": (24.4539, 54.3773),
    "muscat": (23.5880, 58.3829),
    "karachi": (24.8607, 67.0011),
    "dhaka": (23.8103, 90.4125),
    "colombo_city": (6.9271, 79.8612),
    "taipei": (25.0330, 121.5654),
    "seoul": (37.5665, 126.9780),
    "osaka": (34.6937, 135.5023),
    "melbourne": (-37.8136, 144.9631),
    "auckland": (-36.8485, 174.7633),
    "vancouver": (49.2827, -123.1207),
    "toronto": (43.6532, -79.3832),
    "montreal": (45.5017, -73.5673),
    "casablanca": (33.5731, -7.5898),
    "durban": (-29.8587, 31.0218),
    "lima": (-12.0464, -77.0428),
    "bogota": (4.7110, -74.0721),
    "santiago": (-33.4489, -70.6693),
    "lisbon": (38.7223, -9.1393),
    "barcelona": (41.3874, 2.1686),
    "marseille": (43.2965, 5.3698),
    "genoa": (44.4056, 8.9463),
    "antwerp": (51.2194, 4.4025),
    "felixstowe": (51.9638, 1.3511),
    "busan": (35.1796, 129.0756),
}


def _normalize_location(name: str) -> str:
    """Normalize a location name for matching."""
    return name.lower().strip().replace(" ", "_").replace("-", "_").replace(",", "")


def _resolve_coordinates_fallback(location: str) -> Optional[Tuple[float, float]]:
    """
    Try to resolve coordinates from the built-in city database.
    """
    normalized = _normalize_location(location)

    # Direct match
    if normalized in CITY_COORDINATES:
        return CITY_COORDINATES[normalized]

    # Partial match
    for key, coords in CITY_COORDINATES.items():
        if normalized in key or key in normalized:
            return coords

    return None


def _find_nearest_hub(lat: float, lng: float) -> Dict[str, Any]:
    """
    Find the nearest major logistics hub from ports.json
    given a latitude/longitude pair.
    """
    ports = _load_ports()
    best_key = None
    best_distance = float('inf')
    best_port = None

    for key, port in ports.items():
        dist = haversine_distance(lat, lng, port["lat"], port["lng"])
        if dist < best_distance:
            best_distance = dist
            best_key = key
            best_port = port

    return {
        "hub_key": best_key,
        "hub_name": best_port["name"] if best_port else "Unknown",
        "hub_lat": best_port["lat"] if best_port else lat,
        "hub_lng": best_port["lng"] if best_port else lng,
        "distance_to_hub_km": round(best_distance, 1)
    }


async def _resolve_with_llm(location: str, llm) -> Optional[Tuple[float, float]]:
    """
    Use LLM to resolve a location to coordinates.
    """
    prompt = f"""You are a geocoding assistant. Given a location name, return its latitude and longitude.

Location: "{location}"

Respond with ONLY a JSON object in this exact format, no extra text:
{{"lat": <number>, "lng": <number>}}"""

    try:
        response = await llm.ainvoke(prompt)
        content = response.content if hasattr(response, 'content') else str(response)
        json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            lat = float(data.get("lat", 0))
            lng = float(data.get("lng", 0))
            if -90 <= lat <= 90 and -180 <= lng <= 180 and (lat != 0 or lng != 0):
                return (lat, lng)
    except Exception as e:
        print(f"LLM geocoding failed for '{location}': {e}")

    return None


async def hub_resolver_node(state: ShipmentState, llm=None) -> Dict[str, Any]:
    """
    Resolve origin & destination to coordinates and nearest known hubs.
    Pipeline: ports.json direct → city database → LLM geocoding → fail gracefully.
    """
    constraints = state.get("parsed_constraints")
    if not constraints:
        return {
            "resolved_hubs": None,
            "reasoning_trace": [{
                "agent": "Hub Resolver",
                "step": "Resolution Failed",
                "detail": "No parsed constraints available for hub resolution",
                "icon": "📍"
            }],
            "error": "No parsed constraints to resolve hubs from."
        }

    origin_raw = constraints.get("origin", "")
    dest_raw = constraints.get("destination", "")

    resolved = {}

    for label, location_raw in [("origin", origin_raw), ("destination", dest_raw)]:
        # Step 1: Check if already in ports.json
        known_key = find_matching_location(location_raw)
        if known_key:
            coords = get_coordinates(known_key)
            resolved[label] = {
                "original": location_raw,
                "resolved_key": known_key,
                "lat": coords[0],
                "lng": coords[1],
                "nearest_hub": known_key,
                "nearest_hub_name": _load_ports()[known_key]["name"],
                "distance_to_hub_km": 0,
                "method": "direct_match"
            }
            continue

        # Step 2: Try built-in city coordinates
        coords = _resolve_coordinates_fallback(location_raw)
        method = "city_database"

        # Step 3: Try LLM resolution
        if coords is None and llm is not None:
            coords = await _resolve_with_llm(location_raw, llm)
            method = "llm_geocoding"

        if coords is not None:
            hub_info = _find_nearest_hub(coords[0], coords[1])
            resolved[label] = {
                "original": location_raw,
                "resolved_key": hub_info["hub_key"],
                "lat": coords[0],
                "lng": coords[1],
                "nearest_hub": hub_info["hub_key"],
                "nearest_hub_name": hub_info["hub_name"],
                "distance_to_hub_km": hub_info["distance_to_hub_km"],
                "method": method
            }
        else:
            # Final fallback: use location name as-is
            resolved[label] = {
                "original": location_raw,
                "resolved_key": _normalize_location(location_raw),
                "lat": None,
                "lng": None,
                "nearest_hub": None,
                "nearest_hub_name": None,
                "distance_to_hub_km": None,
                "method": "unresolved"
            }

    # Build reasoning detail
    parts = []
    for label in ["origin", "destination"]:
        r = resolved[label]
        if r["method"] == "direct_match":
            parts.append(f"  {label.title()}: {r['original']} → ✅ Known hub: {r['nearest_hub_name']}")
        elif r["method"] in ("city_database", "llm_geocoding"):
            parts.append(
                f"  {label.title()}: {r['original']} → 📍 ({r['lat']:.2f}, {r['lng']:.2f}) "
                f"→ Nearest hub: {r['nearest_hub_name']} ({r['distance_to_hub_km']}km away) "
                f"[via {r['method'].replace('_', ' ')}]"
            )
        else:
            parts.append(f"  {label.title()}: {r['original']} → ⚠️ Could not resolve coordinates")

    return {
        "resolved_hubs": resolved,
        "reasoning_trace": [{
            "agent": "Hub Resolver",
            "step": "Locations Resolved",
            "detail": "Hub resolution results:\n" + "\n".join(parts),
            "icon": "📍",
            "data": resolved
        }]
    }
