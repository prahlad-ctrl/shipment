"""
Simulated port congestion API.
Returns realistic congestion data for major ports including
queue times, berth availability, and estimated delays.
"""

import json
import os
import hashlib
from typing import Dict, Optional
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

_ports_cache: Optional[Dict] = None


def _load_ports() -> Dict:
    global _ports_cache
    if _ports_cache is None:
        with open(os.path.join(DATA_DIR, "ports.json"), "r") as f:
            _ports_cache = json.load(f)
    return _ports_cache


# Base congestion profiles for ports (0-1 scale)
CONGESTION_PROFILES = {
    "dubai": {"base": 0.25, "variability": 0.15, "peak_months": [11, 12, 1]},
    "rotterdam": {"base": 0.45, "variability": 0.20, "peak_months": [9, 10, 11]},
    "singapore": {"base": 0.20, "variability": 0.10, "peak_months": [12, 1, 2]},
    "shanghai": {"base": 0.60, "variability": 0.25, "peak_months": [10, 11, 12]},
    "los_angeles": {"base": 0.55, "variability": 0.30, "peak_months": [8, 9, 10, 11]},
    "mumbai": {"base": 0.50, "variability": 0.20, "peak_months": [10, 11, 12]},
    "london": {"base": 0.35, "variability": 0.15, "peak_months": [11, 12]},
    "hamburg": {"base": 0.40, "variability": 0.15, "peak_months": [9, 10, 11]},
    "new_york": {"base": 0.45, "variability": 0.20, "peak_months": [11, 12, 1]},
    "tokyo": {"base": 0.30, "variability": 0.10, "peak_months": [3, 4]},
    "sydney": {"base": 0.25, "variability": 0.10, "peak_months": [12, 1, 2]},
    "istanbul": {"base": 0.40, "variability": 0.20, "peak_months": [7, 8, 9]},
    "jeddah": {"base": 0.35, "variability": 0.15, "peak_months": [6, 7, 12]},
    "colombo": {"base": 0.30, "variability": 0.15, "peak_months": [12, 1]},
    "hong_kong": {"base": 0.25, "variability": 0.10, "peak_months": [10, 11, 12]},
}


def _deterministic_value(seed: str, base: float, variability: float) -> float:
    """Generate a deterministic value with controlled variability."""
    h = int(hashlib.md5(seed.encode()).hexdigest()[:8], 16)
    variation = (h / 0xFFFFFFFF - 0.5) * 2 * variability
    return max(0.05, min(0.98, base + variation))


def get_port_congestion(port_key: str) -> Dict:
    """
    Get current congestion data for a port.

    Returns congestion level, queue time, berth availability, and delays.
    """
    current_month = datetime.now().month
    profile = CONGESTION_PROFILES.get(
        port_key.lower().replace(" ", "_"),
        {"base": 0.35, "variability": 0.15, "peak_months": []}
    )

    ports = _load_ports()
    port_info = ports.get(port_key.lower().replace(" ", "_"), {})

    # Increase congestion during peak months
    is_peak = current_month in profile["peak_months"]
    base = profile["base"]
    if is_peak:
        base = min(0.95, base + 0.2)

    # Generate deterministic congestion value
    seed = f"{port_key}_{current_month}_{datetime.now().year}"
    congestion_score = _deterministic_value(seed, base, profile["variability"])

    # Map score to level
    if congestion_score >= 0.75:
        level = "critical"
    elif congestion_score >= 0.55:
        level = "high"
    elif congestion_score >= 0.35:
        level = "moderate"
    else:
        level = "low"

    # Calculate derived metrics
    queue_hours = round(congestion_score * 48, 1)  # Up to 48h queue
    berth_availability = round((1 - congestion_score) * 100, 1)  # percentage
    delay_hours = round(congestion_score * 24, 1)  # Up to 24h delay

    # Vessel queue count
    vessel_queue = int(congestion_score * 30)

    return {
        "port_key": port_key,
        "port_name": port_info.get("name", port_key),
        "country": port_info.get("country", "Unknown"),
        "congestion_level": level,
        "congestion_score": round(congestion_score, 2),
        "is_peak_season": is_peak,
        "queue_time_hours": queue_hours,
        "berth_availability_pct": berth_availability,
        "estimated_delay_hours": delay_hours,
        "vessels_in_queue": vessel_queue,
        "advisory": _get_advisory(level, port_key)
    }


def _get_advisory(level: str, port: str) -> str:
    """Generate a human-readable advisory based on congestion level."""
    advisories = {
        "low": f"Normal operations at {port}. No significant delays expected.",
        "moderate": f"Moderate traffic at {port}. Minor delays possible, plan for 4-8 hour buffer.",
        "high": f"Heavy congestion at {port}. Significant delays likely. Consider alternative ports or timing.",
        "critical": f"Critical congestion at {port}. Severe delays expected (24h+). Strongly recommend alternative routing."
    }
    return advisories.get(level, f"Unknown conditions at {port}.")


def get_congestion_for_route(port_keys: list) -> Dict:
    """
    Get congestion data for all ports along a route.
    Returns individual port data plus summary.
    """
    port_data = []
    total_delay = 0
    worst_congestion = 0
    bottleneck_port = None

    for port_key in port_keys:
        data = get_port_congestion(port_key)
        port_data.append(data)
        total_delay += data["estimated_delay_hours"]
        if data["congestion_score"] > worst_congestion:
            worst_congestion = data["congestion_score"]
            bottleneck_port = data["port_name"]

    # Overall assessment
    if worst_congestion >= 0.75:
        overall = "critical"
    elif worst_congestion >= 0.55:
        overall = "high"
    elif worst_congestion >= 0.35:
        overall = "moderate"
    else:
        overall = "low"

    return {
        "overall_congestion": overall,
        "overall_congestion_score": round(worst_congestion, 2),
        "total_estimated_delay_hours": round(total_delay, 1),
        "bottleneck_port": bottleneck_port,
        "port_breakdown": port_data
    }
