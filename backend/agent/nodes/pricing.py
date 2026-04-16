"""
Pricing Agent Node.
Calculates cost breakdowns for each candidate route using the pricing simulator.
"""

from typing import Dict, Any, List
from agent.state import ShipmentState
from tools.pricing_simulator import calculate_freight_cost, get_best_price


async def pricing_node(state: ShipmentState, llm=None) -> Dict[str, Any]:
    """
    Calculate pricing for all candidate routes.
    Generates itemized cost breakdowns per route.
    """
    routes = state.get("route_candidates", [])
    constraints = state.get("parsed_constraints", {})
    budget = constraints.get("budget_usd")
    weight_kg = constraints.get("weight_kg", 100)

    if not routes:
        return {
            "pricing_data": [],
            "reasoning_trace": [{
                "agent": "Pricing",
                "step": "No Routes to Price",
                "detail": "No route candidates available for pricing",
                "icon": "💰"
            }]
        }

    pricing_results = []
    cheapest = float('inf')
    most_expensive = 0

    for route in routes:
        total_cost = 0
        leg_costs = []

        for leg in route.get("legs", []):
            mode = leg.get("mode", "sea")
            distance = leg.get("distance_km", 1000)

            cost = calculate_freight_cost(
                mode=mode,
                weight_kg=weight_kg,
                distance_km=distance,
                carrier_id=None
            )
            total_cost += cost["total"]
            leg_costs.append(cost)

        # Aggregate cost breakdown across legs
        aggregated = {
            "carrier_name": leg_costs[0]["carrier_name"] if leg_costs else "Unknown",
            "freight": round(sum(c["freight"] for c in leg_costs), 2),
            "fuel_surcharge": round(sum(c["fuel_surcharge"] for c in leg_costs), 2),
            "customs_and_docs": round(sum(c["customs_and_docs"] for c in leg_costs), 2),
            "insurance": round(sum(c["insurance"] for c in leg_costs), 2),
            "handling": round(sum(c["handling"] for c in leg_costs), 2),
            "total": round(total_cost, 2),
            "currency": "USD"
        }

        if len(leg_costs) > 1:
            carriers = list(set(c["carrier_name"] for c in leg_costs))
            aggregated["carrier_name"] = " + ".join(carriers)

        within_budget = None
        budget_delta = None
        if budget:
            within_budget = total_cost <= budget
            budget_delta = round(budget - total_cost, 2)

        cheapest = min(cheapest, total_cost)
        most_expensive = max(most_expensive, total_cost)

        pricing_results.append({
            "route_id": route["id"],
            "cost_breakdown": aggregated,
            "within_budget": within_budget,
            "budget_delta": budget_delta
        })

    # Build reasoning detail
    price_summary = "\n".join(
        f"  • {p['route_id']}: ${p['cost_breakdown']['total']:,.2f}"
        + (f" ({'✅ within' if p['within_budget'] else '❌ over'} budget by ${abs(p['budget_delta']):,.2f})" if p['within_budget'] is not None else "")
        for p in pricing_results
    )

    return {
        "pricing_data": pricing_results,
        "reasoning_trace": [{
            "agent": "Pricing",
            "step": f"Pricing Complete — Range: ${cheapest:,.2f} to ${most_expensive:,.2f}",
            "detail": f"Cost estimates per route:\n{price_summary}",
            "icon": "💰",
            "data": {
                "cheapest": cheapest,
                "most_expensive": most_expensive,
                "routes_in_budget": sum(1 for p in pricing_results if p.get("within_budget") is True)
            }
        }]
    }
