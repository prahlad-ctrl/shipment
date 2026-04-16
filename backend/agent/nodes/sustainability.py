"""
Sustainability Agent Node.
Calculates carbon emissions (CO2 equivalent) for each candidate route
and assigns a "Green Score" to help users make eco-friendly decisions.
"""

from typing import Dict, Any, List
from agent.state import ShipmentState


# ── Emission factors (grams CO2e per tonne-km) ──────────────────────────────
# Source: International Transport Forum (ITF) / EPA estimates
EMISSION_FACTORS = {
    "air": 600,       # ~500-800g CO2e per tonne-km (high altitude forcing)
    "sea": 20,        # ~10-40g CO2e per tonne-km (most efficient long-haul)
    "road": 100,      # ~60-150g CO2e per tonne-km (trucks)
    "multimodal": 80, # average estimate for mixed modes
}


def _calculate_route_emissions(route: Dict, weight_kg: float) -> Dict[str, Any]:
    """
    Calculate CO2 emissions for a single route.
    Returns emissions in kg CO2e and a green score (0-100).
    """
    total_emissions_g = 0
    leg_emissions = []

    weight_tonnes = weight_kg / 1000.0

    for leg in route.get("legs", []):
        mode = leg.get("mode", "sea")
        distance_km = leg.get("distance_km", 0)
        factor = EMISSION_FACTORS.get(mode, EMISSION_FACTORS["sea"])

        emissions_g = distance_km * weight_tonnes * factor
        leg_emissions.append({
            "from": leg.get("from_location", ""),
            "to": leg.get("to_location", ""),
            "mode": mode,
            "distance_km": distance_km,
            "emissions_kg": round(emissions_g / 1000, 2),
            "factor_used": factor
        })
        total_emissions_g += emissions_g

    total_emissions_kg = round(total_emissions_g / 1000, 2)

    return {
        "total_emissions_kg": total_emissions_kg,
        "leg_breakdown": leg_emissions,
    }


def _calculate_green_scores(all_emissions: List[float]) -> List[float]:
    """
    Calculate green scores for each route relative to all alternatives.
    100 = cleanest route, lower = dirtier route.
    Uses inverse scaling: lowest emissions = highest score.
    """
    if not all_emissions:
        return []

    min_em = min(all_emissions)
    max_em = max(all_emissions)
    emission_range = max_em - min_em

    scores = []
    for em in all_emissions:
        if emission_range == 0:
            scores.append(85.0)  # All routes same emissions
        else:
            # Inverse: lowest emissions = 100, highest = 15
            normalized = (em - min_em) / emission_range
            score = 100 - (normalized * 85)  # Range: 15-100
            scores.append(round(score, 1))

    return scores


def _get_eco_label(green_score: float) -> str:
    """Get a human-readable eco label from green score."""
    if green_score >= 85:
        return "Excellent"
    elif green_score >= 65:
        return "Good"
    elif green_score >= 40:
        return "Moderate"
    else:
        return "Poor"


async def sustainability_node(state: ShipmentState, llm=None) -> Dict[str, Any]:
    """
    Calculate carbon footprint and green scores for all candidate routes.
    Runs in parallel with pricing, weather, and congestion agents.
    """
    routes = state.get("route_candidates", [])
    constraints = state.get("parsed_constraints", {})
    weight_kg = constraints.get("weight_kg") or 500.0

    if not routes:
        return {
            "sustainability_data": [],
            "reasoning_trace": [{
                "agent": "Sustainability",
                "step": "No Routes to Assess",
                "detail": "No route candidates available for emissions analysis",
                "icon": "🌱"
            }]
        }

    # Calculate emissions for all routes
    sustainability_results = []
    all_emissions = []

    for route in routes:
        emissions = _calculate_route_emissions(route, weight_kg)
        all_emissions.append(emissions["total_emissions_kg"])
        sustainability_results.append({
            "route_id": route["id"],
            **emissions
        })

    # Calculate relative green scores
    green_scores = _calculate_green_scores(all_emissions)

    # Attach green scores
    for i, result in enumerate(sustainability_results):
        result["green_score"] = green_scores[i]
        result["eco_label"] = _get_eco_label(green_scores[i])

    # Find the greenest route
    greenest_idx = all_emissions.index(min(all_emissions))
    greenest = sustainability_results[greenest_idx]

    # Build reasoning
    emissions_summary = "\n".join(
        f"  {'🌿' if r['green_score'] >= 75 else '🍂' if r['green_score'] >= 40 else '🏭'} "
        f"{r['route_id']}: {r['total_emissions_kg']} kg CO2e "
        f"(Green Score: {r['green_score']}/100 — {r['eco_label']})"
        for r in sustainability_results
    )

    # Show emission factor comparison
    factor_note = (
        f"\n\n📊 Emission factors: Air={EMISSION_FACTORS['air']}g, "
        f"Sea={EMISSION_FACTORS['sea']}g, Road={EMISSION_FACTORS['road']}g per tonne-km"
    )

    return {
        "sustainability_data": sustainability_results,
        "reasoning_trace": [{
            "agent": "Sustainability",
            "step": f"Emissions Calculated — Greenest: {greenest['route_id']}",
            "detail": (
                f"Carbon footprint per route (for {weight_kg}kg shipment):\n"
                f"{emissions_summary}{factor_note}"
            ),
            "icon": "🌱",
            "data": {
                "greenest_route": greenest["route_id"],
                "greenest_emissions_kg": greenest["total_emissions_kg"],
                "worst_emissions_kg": max(all_emissions),
            }
        }]
    }
