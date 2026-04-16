"""
Risk Scenario Agent Node.
Modifies route feasibility and penalties based on global "world events"
such as canal blockages, port strikes, or extreme weather.
Runs early in the pipeline to set the global risk context.
"""

from typing import Dict, Any, List
from agent.state import ShipmentState


# ── World Event Definitions ──────────────────────────────────────────────────
WORLD_EVENTS = {
    "normal": {
        "name": "Normal Conditions",
        "description": "No special global disruptions. Standard operations.",
        "icon": "✅",
        "impacts": []
    },
    "suez_canal_blocked": {
        "name": "Suez Canal Blocked",
        "description": (
            "The Suez Canal is blocked, forcing vessels to reroute around the "
            "Cape of Good Hope. Adds significant time and cost to any sea route "
            "through the Mediterranean-Red Sea corridor."
        ),
        "icon": "🚫",
        "impacts": [
            {
                "condition": "sea_through_suez",
                "affected_corridors": [
                    "dubai_rotterdam", "mumbai_london", "singapore_hamburg",
                    "dubai_hamburg", "mumbai_rotterdam", "jeddah"
                ],
                "time_penalty_days": 10,
                "cost_penalty_usd": 5000,
                "description": "Rerouting around Cape of Good Hope (+10 days, +$5000)"
            }
        ]
    },
    "port_strike": {
        "name": "European Port Strike",
        "description": (
            "Major European ports (Rotterdam, Hamburg) are on strike. "
            "Sea arrivals face severe delays. Air freight is unaffected."
        ),
        "icon": "⚠️",
        "impacts": [
            {
                "condition": "european_port_arrival",
                "affected_ports": ["rotterdam", "hamburg", "london", "antwerp", "felixstowe"],
                "time_penalty_days": 5,
                "cost_penalty_usd": 2000,
                "description": "Port strike delays at European ports (+5 days, +$2000)"
            }
        ]
    },
    "atlantic_storm": {
        "name": "Atlantic Storm Season",
        "description": (
            "Severe storms across the Atlantic Ocean. All trans-Atlantic "
            "routes face weather delays and increased risk."
        ),
        "icon": "🌀",
        "impacts": [
            {
                "condition": "trans_atlantic",
                "affected_corridors": ["new_york", "los_angeles", "atlantic"],
                "time_penalty_days": 3,
                "cost_penalty_usd": 1500,
                "weather_risk_increase": 0.4,
                "description": "Atlantic storm delays (+3 days, +$1500, elevated weather risk)"
            }
        ]
    }
}


def _check_route_affected(route: Dict, impact: Dict) -> bool:
    """
    Check if a route is affected by a specific impact rule.
    """
    condition = impact.get("condition", "")

    # Check corridor-level impacts
    if "affected_corridors" in impact:
        route_id = route.get("id", "").lower()
        route_name = route.get("name", "").lower()
        for corridor in impact["affected_corridors"]:
            if corridor in route_id or corridor in route_name:
                return True

        # Check leg endpoints
        for leg in route.get("legs", []):
            from_loc = leg.get("from_location", "").lower()
            to_loc = leg.get("to_location", "").lower()
            for corridor in impact["affected_corridors"]:
                if corridor in from_loc or corridor in to_loc:
                    return True

    # Check port-level impacts
    if "affected_ports" in impact:
        for leg in route.get("legs", []):
            from_loc = leg.get("from_location", "").lower()
            to_loc = leg.get("to_location", "").lower()
            for port in impact["affected_ports"]:
                if port in from_loc or port in to_loc:
                    # For port strikes, only sea/road modes at those ports are affected
                    if condition == "european_port_arrival" and leg.get("mode") == "air":
                        continue
                    return True

    return False


async def risk_scenario_node(state: ShipmentState, llm=None) -> Dict[str, Any]:
    """
    Process world events and calculate route-specific risk penalties.
    This node reads the world_event from state and produces a risk assessment
    that downstream agents (evaluator, decision) use to adjust scores.
    """
    world_event = state.get("world_event", "normal") or "normal"
    routes = state.get("route_candidates", [])

    event_config = WORLD_EVENTS.get(world_event, WORLD_EVENTS["normal"])

    if world_event == "normal" or not event_config.get("impacts"):
        return {
            "risk_scenario": {
                "event": world_event,
                "event_name": event_config["name"],
                "description": event_config["description"],
                "affected_routes": [],
                "penalties": {}
            },
            "reasoning_trace": [{
                "agent": "Risk Scenario",
                "step": f"World Conditions: {event_config['name']}",
                "detail": f"{event_config['icon']} {event_config['description']}",
                "icon": event_config["icon"],
                "data": {"event": world_event, "affected_count": 0}
            }]
        }

    # Check each route against all impacts
    penalties = {}
    affected_routes = []
    impact_details = []

    for route in routes:
        route_id = route["id"]
        route_penalty = {
            "time_penalty_days": 0,
            "cost_penalty_usd": 0,
            "weather_risk_increase": 0,
            "descriptions": []
        }

        for impact in event_config["impacts"]:
            if _check_route_affected(route, impact):
                route_penalty["time_penalty_days"] += impact.get("time_penalty_days", 0)
                route_penalty["cost_penalty_usd"] += impact.get("cost_penalty_usd", 0)
                route_penalty["weather_risk_increase"] += impact.get("weather_risk_increase", 0)
                route_penalty["descriptions"].append(impact["description"])

        if route_penalty["time_penalty_days"] > 0 or route_penalty["cost_penalty_usd"] > 0:
            penalties[route_id] = route_penalty
            affected_routes.append(route_id)
            impact_details.append(
                f"  ⚠️ {route['name']}:\n"
                f"     +{route_penalty['time_penalty_days']} days, "
                f"+${route_penalty['cost_penalty_usd']:,} cost penalty\n"
                f"     Reason: {'; '.join(route_penalty['descriptions'])}"
            )

    # Build reasoning detail
    if affected_routes:
        detail = (
            f"{event_config['icon']} **{event_config['name']}**\n"
            f"{event_config['description']}\n\n"
            f"Affected routes ({len(affected_routes)}/{len(routes)}):\n"
            + "\n".join(impact_details)
        )
    else:
        detail = (
            f"{event_config['icon']} **{event_config['name']}**\n"
            f"{event_config['description']}\n\n"
            f"No candidate routes are affected by this event."
        )

    return {
        "risk_scenario": {
            "event": world_event,
            "event_name": event_config["name"],
            "description": event_config["description"],
            "affected_routes": affected_routes,
            "penalties": penalties
        },
        "reasoning_trace": [{
            "agent": "Risk Scenario",
            "step": f"⚡ {event_config['name']} — {len(affected_routes)} routes affected",
            "detail": detail,
            "icon": event_config["icon"],
            "data": {
                "event": world_event,
                "affected_count": len(affected_routes),
                "penalties": penalties
            }
        }]
    }
