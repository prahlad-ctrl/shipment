"""
Port Congestion Agent Node.
Checks congestion levels at ports/hubs along each candidate route.
"""

from typing import Dict, Any
from agent.state import ShipmentState
from tools.port_simulator import get_port_congestion, get_congestion_for_route


async def port_congestion_node(state: ShipmentState, llm=None) -> Dict[str, Any]:
    """
    Check port congestion for all candidate routes.
    Identifies bottleneck ports and estimates delays.
    """
    routes = state.get("route_candidates", [])

    if not routes:
        return {
            "congestion_data": [],
            "reasoning_trace": [{
                "agent": "Port Congestion",
                "step": "No Routes to Check",
                "detail": "No route candidates available for congestion check",
                "icon": "⚓"
            }]
        }

    congestion_results = []
    worst_congestion = "low"
    congestion_order = {"low": 0, "moderate": 1, "high": 2, "critical": 3}

    for route in routes:
        # Collect port locations (sea legs mainly)
        port_keys = []
        for leg in route.get("legs", []):
            if leg["from_location"] not in port_keys:
                port_keys.append(leg["from_location"])
            if leg["to_location"] not in port_keys:
                port_keys.append(leg["to_location"])

        congestion = get_congestion_for_route(port_keys)

        congestion_result = {
            "route_id": route["id"],
            "overall_congestion": congestion["overall_congestion"],
            "overall_score": congestion["overall_congestion_score"],
            "total_delay_hours": congestion["total_estimated_delay_hours"],
            "bottleneck_port": congestion["bottleneck_port"],
            "port_breakdown": [
                {
                    "port_name": p["port_name"],
                    "congestion_level": p["congestion_level"],
                    "congestion_score": p["congestion_score"],
                    "queue_time_hours": p["queue_time_hours"],
                    "berth_availability_pct": p["berth_availability_pct"],
                    "estimated_delay_hours": p["estimated_delay_hours"],
                    "vessels_in_queue": p["vessels_in_queue"],
                    "advisory": p["advisory"]
                }
                for p in congestion["port_breakdown"]
            ]
        }

        congestion_results.append(congestion_result)

        if congestion_order.get(congestion["overall_congestion"], 0) > congestion_order.get(worst_congestion, 0):
            worst_congestion = congestion["overall_congestion"]

    # Build reasoning
    congestion_summary = "\n".join(
        f"  • {c['route_id']}: {c['overall_congestion'].upper()} "
        f"(bottleneck: {c['bottleneck_port']}, delay: +{c['total_delay_hours']}h)"
        for c in congestion_results
    )

    return {
        "congestion_data": congestion_results,
        "reasoning_trace": [{
            "agent": "Port Congestion",
            "step": f"Congestion Check — Worst: {worst_congestion.upper()}",
            "detail": f"Port congestion per route:\n{congestion_summary}",
            "icon": "⚓",
            "data": {
                "worst_congestion": worst_congestion,
                "bottleneck_ports": list(set(c["bottleneck_port"] for c in congestion_results if c["bottleneck_port"]))
            }
        }]
    }
