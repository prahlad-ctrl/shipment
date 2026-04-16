"""
Route Generator Agent Node.
Generates candidate routes across multiple transport modes.
Uses pre-defined corridors from the routes database and generates
alternatives dynamically when needed.
"""

import json
import os
from typing import Dict, Any, List
from agent.state import ShipmentState
from tools.geo_utils import (
    find_matching_location,
    calculate_distance,
    get_route_waypoints,
    get_coordinates,
    is_land_connected
)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")


def _load_routes_db() -> Dict:
    with open(os.path.join(DATA_DIR, "routes_db.json"), "r") as f:
        return json.load(f)


def _load_carriers() -> Dict:
    with open(os.path.join(DATA_DIR, "carriers.json"), "r") as f:
        return json.load(f)


def _generate_direct_routes(
    origin: str,
    destination: str,
    weight_kg: float
) -> List[Dict[str, Any]]:
    """Generate basic direct routes when no pre-defined corridor exists."""
    distance = calculate_distance(origin, destination)
    if distance is None:
        distance = 5000  # default fallback

    routes = []
    carriers = _load_carriers()

    # Air route
    air_hours = distance / 850 + 4  # flight time + ground handling
    routes.append({
        "id": f"{origin}_{destination}_air_direct",
        "name": f"Direct Air Freight ({origin} → {destination})",
        "mode": "air",
        "legs": [{
            "from_location": origin,
            "to_location": destination,
            "mode": "air",
            "carrier": carriers["air"][0]["name"] if carriers.get("air") else "Air Carrier",
            "distance_km": round(distance, 0),
            "duration_hours": round(air_hours, 1)
        }],
        "total_distance_km": round(distance, 0),
        "estimated_days": round(air_hours / 24 + 0.5, 1)  # +0.5 for customs
    })

    # Sea route (only if distance > 500km)
    if distance > 500:
        sea_distance = distance * 1.3  # sea routes are longer
        sea_hours = sea_distance / 35 + 24  # sailing + port time
        routes.append({
            "id": f"{origin}_{destination}_sea_direct",
            "name": f"Direct Sea Freight ({origin} → {destination})",
            "mode": "sea",
            "legs": [{
                "from_location": origin,
                "to_location": destination,
                "mode": "sea",
                "carrier": carriers["sea"][0]["name"] if carriers.get("sea") else "Sea Carrier",
                "distance_km": round(sea_distance, 0),
                "duration_hours": round(sea_hours, 1)
            }],
            "total_distance_km": round(sea_distance, 0),
            "estimated_days": round(sea_hours / 24, 1)
        })

    # Road route (only if distance < 5000km)
    land_connected = is_land_connected(origin, destination)

    if distance < 5000 and land_connected:
        road_distance = distance * 1.2
        road_hours = road_distance / 60 + 8  # driving + rest stops
        routes.append({
            "id": f"{origin}_{destination}_road_direct",
            "name": f"Road Freight ({origin} → {destination})",
            "mode": "road",
            "legs": [{
                "from_location": origin,
                "to_location": destination,
                "mode": "road",
                "carrier": carriers["road"][0]["name"] if carriers.get("road") else "Road Carrier",
                "distance_km": round(road_distance, 0),
                "duration_hours": round(road_hours, 1)
            }],
            "total_distance_km": round(road_distance, 0),
            "estimated_days": round(road_hours / 24, 1)
        })

    # Rail route (only if distance > 300 and distance < 12000km and on same landmass)
    if 300 < distance < 12000 and land_connected:
        rail_distance = distance * 1.15
        rail_hours = rail_distance / 45 + 16  # driving + terminal time
        routes.append({
            "id": f"{origin}_{destination}_rail_direct",
            "name": f"Rail Freight ({origin} → {destination})",
            "mode": "rail",
            "legs": [{
                "from_location": origin,
                "to_location": destination,
                "mode": "rail",
                "carrier": carriers["rail"][0]["name"] if carriers.get("rail") else "Rail Carrier",
                "distance_km": round(rail_distance, 0),
                "duration_hours": round(rail_hours, 1)
            }],
            "total_distance_km": round(rail_distance, 0),
            "estimated_days": round(rail_hours / 24, 1)
        })

    return routes


def _convert_corridor_to_route(corridor: Dict) -> Dict[str, Any]:
    """Convert a routes_db corridor to a RouteCandidate format."""
    legs = []
    for leg in corridor["legs"]:
        legs.append({
            "from_location": leg["from"],
            "to_location": leg["to"],
            "mode": leg["mode"],
            "carrier": None,  # Will be filled by pricing agent
            "distance_km": leg["distance_km"],
            "duration_hours": leg["typical_hours"]
        })

    return {
        "id": corridor["id"],
        "name": f"{corridor['mode'].title()} Route: {corridor['origin'].title()} → {corridor['destination'].title()}",
        "mode": corridor["mode"],
        "legs": legs,
        "total_distance_km": corridor["total_distance_km"],
        "estimated_days": corridor["typical_days"],
        "notes": corridor.get("notes", "")
    }


def _add_waypoints(route: Dict) -> Dict:
    """Add map visualization waypoints to a route."""
    all_waypoints = []
    for leg in route["legs"]:
        wp = get_route_waypoints(leg["from_location"], leg["to_location"], leg.get("mode", "air"))
        if wp:
            all_waypoints.extend([[lat, lng] for lat, lng in wp])
    route["waypoints"] = all_waypoints
    return route


async def route_generator_node(state: ShipmentState, llm=None) -> Dict[str, Any]:
    """
    Generate candidate routes based on parsed constraints.
    First checks pre-defined corridors, then generates dynamic routes.
    """
    constraints = state["parsed_constraints"]
    if not constraints:
        return {
            "route_candidates": [],
            "reasoning_trace": [{
                "agent": "Route Generator",
                "step": "Generation Failed",
                "detail": "No parsed constraints available",
                "icon": "❌"
            }],
            "error": "No parsed constraints to generate routes from."
        }

    origin = constraints["origin"].lower().replace(" ", "_")
    destination = constraints["destination"].lower().replace(" ", "_")
    weight_kg = constraints.get("weight_kg", 100)

    # Match to known locations
    origin_key = find_matching_location(origin) or origin
    dest_key = find_matching_location(destination) or destination

    routes_db = _load_routes_db()
    candidates = []

    # Find matching pre-defined corridors
    for corridor in routes_db.get("corridors", []):
        corridor_origin = find_matching_location(corridor["origin"]) or corridor["origin"]
        corridor_dest = find_matching_location(corridor["destination"]) or corridor["destination"]

        if corridor_origin == origin_key and corridor_dest == dest_key:
            route = _convert_corridor_to_route(corridor)
            route = _add_waypoints(route)
            candidates.append(route)

    # If no pre-defined corridors, generate dynamic routes
    if not candidates:
        candidates = _generate_direct_routes(origin_key, dest_key, weight_kg)
        for route in candidates:
            route = _add_waypoints(route)

    # Ensure we have at least 2 and at most 5 candidates
    if len(candidates) > 5:
        candidates = candidates[:5]

    # Generate summary for reasoning
    mode_summary = ", ".join(set(r["mode"] for r in candidates))
    route_names = "\n".join(f"  • {r['name']} ({r['estimated_days']} days, {r['total_distance_km']}km)" for r in candidates)

    return {
        "route_candidates": candidates,
        "reasoning_trace": [{
            "agent": "Route Generator",
            "step": f"Generated {len(candidates)} Candidate Routes",
            "detail": (
                f"Found routes via: {mode_summary}\n{route_names}"
            ),
            "icon": "🗺️",
            "data": {"route_count": len(candidates), "modes": list(set(r["mode"] for r in candidates))}
        }]
    }
