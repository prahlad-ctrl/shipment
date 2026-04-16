"""
Simulated weather conditions API.
Returns weather risk assessments for route corridors, simulating
real-world weather patterns (monsoons, winter storms, etc.).
"""

import random
import hashlib
from typing import Dict, List, Optional
from datetime import datetime


# Known weather risk zones with seasonal patterns
WEATHER_ZONES = {
    "arabian_sea": {
        "regions": ["dubai", "mumbai", "jeddah", "colombo"],
        "risks": {
            "monsoon": {"months": [6, 7, 8, 9], "severity": "high", "description": "Southwest monsoon season"},
            "cyclone": {"months": [5, 6, 10, 11], "severity": "severe", "description": "Cyclone season"},
            "calm": {"months": [1, 2, 3, 4, 12], "severity": "low", "description": "Calm seas"}
        }
    },
    "north_atlantic": {
        "regions": ["rotterdam", "hamburg", "london", "new_york"],
        "risks": {
            "winter_storm": {"months": [11, 12, 1, 2, 3], "severity": "high", "description": "North Atlantic winter storms"},
            "fog": {"months": [3, 4, 5], "severity": "medium", "description": "Dense fog conditions"},
            "calm": {"months": [6, 7, 8, 9, 10], "severity": "low", "description": "Favorable conditions"}
        }
    },
    "south_china_sea": {
        "regions": ["singapore", "hong_kong", "shanghai", "tokyo"],
        "risks": {
            "typhoon": {"months": [7, 8, 9, 10], "severity": "severe", "description": "Typhoon season"},
            "winter_monsoon": {"months": [11, 12, 1, 2], "severity": "medium", "description": "Northeast monsoon"},
            "calm": {"months": [3, 4, 5, 6], "severity": "low", "description": "Calm conditions"}
        }
    },
    "pacific": {
        "regions": ["los_angeles", "tokyo", "sydney"],
        "risks": {
            "el_nino": {"months": [1, 2, 3, 11, 12], "severity": "medium", "description": "El Niño weather patterns"},
            "storm": {"months": [7, 8, 9], "severity": "high", "description": "Pacific storm season"},
            "calm": {"months": [4, 5, 6, 10], "severity": "low", "description": "Clear conditions"}
        }
    },
    "mediterranean": {
        "regions": ["istanbul"],
        "risks": {
            "meltemi": {"months": [7, 8], "severity": "medium", "description": "Strong dry winds"},
            "winter": {"months": [12, 1, 2], "severity": "medium", "description": "Winter storms"},
            "calm": {"months": [3, 4, 5, 6, 9, 10, 11], "severity": "low", "description": "Mild conditions"}
        }
    }
}

SEVERITY_SCORES = {"low": 0.1, "medium": 0.4, "high": 0.7, "severe": 0.95}
SEVERITY_DELAYS = {"low": 0, "medium": 4, "high": 12, "severe": 36}


def _get_zone_for_location(location: str) -> Optional[str]:
    """Find which weather zone a location belongs to."""
    loc_lower = location.lower().replace(" ", "_")
    for zone_name, zone_data in WEATHER_ZONES.items():
        for region in zone_data["regions"]:
            if loc_lower in region or region in loc_lower:
                return zone_name
    return None


def _deterministic_random(seed_str: str, min_val: float = 0, max_val: float = 1) -> float:
    """Generate a deterministic 'random' float from a seed string."""
    h = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
    return min_val + (h / 0xFFFFFFFF) * (max_val - min_val)


def get_weather_for_location(location: str) -> Dict:
    """
    Get current weather conditions for a location.
    Uses current month to determine seasonal patterns.
    """
    current_month = datetime.now().month
    zone_name = _get_zone_for_location(location)

    if zone_name is None:
        return {
            "location": location,
            "zone": "unknown",
            "risk_level": "low",
            "risk_score": 0.15,
            "conditions": "No specific weather data available",
            "estimated_delay_hours": 0,
            "wind_speed_knots": 8,
            "wave_height_m": 1.0,
            "visibility_km": 15
        }

    zone = WEATHER_ZONES[zone_name]

    # Find current risk based on month
    active_risk = None
    for risk_name, risk_data in zone["risks"].items():
        if current_month in risk_data["months"]:
            if active_risk is None or SEVERITY_SCORES[risk_data["severity"]] > SEVERITY_SCORES.get(active_risk.get("severity", "low"), 0):
                active_risk = {"name": risk_name, **risk_data}

    if active_risk is None:
        active_risk = {"name": "calm", "severity": "low", "description": "Normal conditions"}

    severity = active_risk["severity"]
    base_score = SEVERITY_SCORES.get(severity, 0.1)

    # Add some variation
    seed = f"{location}_{current_month}_{zone_name}"
    variation = _deterministic_random(seed, -0.1, 0.1)
    risk_score = max(0.05, min(1.0, base_score + variation))

    # Generate weather details
    wind = _deterministic_random(f"wind_{seed}", 5, 15 + base_score * 35)
    waves = _deterministic_random(f"wave_{seed}", 0.5, 1.5 + base_score * 6)
    visibility = _deterministic_random(f"vis_{seed}", 20 - base_score * 18, 20)

    return {
        "location": location,
        "zone": zone_name,
        "risk_level": severity,
        "risk_score": round(risk_score, 2),
        "conditions": active_risk["description"],
        "weather_event": active_risk["name"],
        "estimated_delay_hours": SEVERITY_DELAYS.get(severity, 0),
        "wind_speed_knots": round(wind, 1),
        "wave_height_m": round(waves, 1),
        "visibility_km": round(visibility, 1)
    }


def get_weather_for_route(locations: List[str]) -> Dict:
    """
    Get weather assessment for a full route (list of waypoints).
    Returns the overall risk and per-location breakdown.
    """
    location_weather = []
    max_risk_score = 0
    total_delay = 0
    worst_conditions = []

    for loc in locations:
        weather = get_weather_for_location(loc)
        location_weather.append(weather)
        if weather["risk_score"] > max_risk_score:
            max_risk_score = weather["risk_score"]
        total_delay += weather["estimated_delay_hours"]
        if weather["risk_level"] in ("high", "severe"):
            worst_conditions.append(f"{weather['conditions']} near {loc}")

    # Overall risk level
    if max_risk_score >= 0.8:
        overall_risk = "severe"
    elif max_risk_score >= 0.5:
        overall_risk = "high"
    elif max_risk_score >= 0.3:
        overall_risk = "medium"
    else:
        overall_risk = "low"

    return {
        "overall_risk_level": overall_risk,
        "overall_risk_score": round(max_risk_score, 2),
        "total_estimated_delay_hours": total_delay,
        "worst_conditions": worst_conditions if worst_conditions else ["No significant weather risks"],
        "location_breakdown": location_weather
    }
