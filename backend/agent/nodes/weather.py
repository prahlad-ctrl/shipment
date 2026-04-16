"""
Weather Agent Node.
Assesses weather risks along each candidate route.
"""

from typing import Dict, Any
from agent.state import ShipmentState
from tools.weather_simulator import get_weather_for_route, get_weather_for_location


async def weather_node(state: ShipmentState, llm=None) -> Dict[str, Any]:
    """
    Assess weather conditions for all candidate routes.
    Checks weather at each waypoint/port along each route.
    """
    routes = state.get("route_candidates", [])

    if not routes:
        return {
            "weather_data": [],
            "reasoning_trace": [{
                "agent": "Weather",
                "step": "No Routes to Assess",
                "detail": "No route candidates available for weather assessment",
                "icon": "🌤️"
            }]
        }

    weather_results = []
    highest_risk = "low"
    risk_order = {"low": 0, "medium": 1, "high": 2, "severe": 3}

    for route in routes:
        # Collect all locations along the route
        locations = []
        for leg in route.get("legs", []):
            if leg["from_location"] not in locations:
                locations.append(leg["from_location"])
            if leg["to_location"] not in locations:
                locations.append(leg["to_location"])

        # Get weather for the route corridor
        weather = get_weather_for_route(locations)

        weather_result = {
            "route_id": route["id"],
            "overall_risk_level": weather["overall_risk_level"],
            "overall_risk_score": weather["overall_risk_score"],
            "total_delay_hours": weather["total_estimated_delay_hours"],
            "worst_conditions": weather["worst_conditions"],
            "location_breakdown": [
                {
                    "location": loc["location"],
                    "zone": loc["zone"],
                    "risk_level": loc["risk_level"],
                    "risk_score": loc["risk_score"],
                    "conditions": loc["conditions"],
                    "estimated_delay_hours": loc["estimated_delay_hours"],
                    "wind_speed_knots": loc["wind_speed_knots"],
                    "wave_height_m": loc["wave_height_m"]
                }
                for loc in weather["location_breakdown"]
            ]
        }

        weather_results.append(weather_result)

        if risk_order.get(weather["overall_risk_level"], 0) > risk_order.get(highest_risk, 0):
            highest_risk = weather["overall_risk_level"]

    # Build reasoning
    weather_summary = "\n".join(
        f"  • {w['route_id']}: {w['overall_risk_level'].upper()} risk (score: {w['overall_risk_score']}, delay: +{w['total_delay_hours']}h)"
        for w in weather_results
    )

    risk_warnings = []
    for w in weather_results:
        for cond in w["worst_conditions"]:
            if cond != "No significant weather risks" and cond not in risk_warnings:
                risk_warnings.append(cond)

    detail = f"Weather assessment per route:\n{weather_summary}"
    if risk_warnings:
        detail += f"\n\n⚠️ Active warnings: {'; '.join(risk_warnings)}"

    return {
        "weather_data": weather_results,
        "reasoning_trace": [{
            "agent": "Weather",
            "step": f"Weather Assessment — Highest Risk: {highest_risk.upper()}",
            "detail": detail,
            "icon": "🌤️",
            "data": {
                "highest_risk": highest_risk,
                "routes_with_warnings": len(risk_warnings)
            }
        }]
    }
