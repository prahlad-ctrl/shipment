"""
Decision Agent Node.
Makes the final route recommendation with justified reasoning.
Uses LLM for natural language reasoning with algorithmic fallback.
"""

import json
import re
from typing import Dict, Any
from agent.state import ShipmentState


def _algorithmic_decision(scored_routes: list, constraints: dict, original_query: str) -> Dict[str, Any]:
    """Generate decision reasoning algorithmically."""
    if not scored_routes:
        return {
            "reasoning_summary": "No viable routes found for this shipment.",
            "trade_off_analysis": "Unable to generate trade-off analysis without route options."
        }

    winner = scored_routes[0]
    runner_up = scored_routes[1] if len(scored_routes) > 1 else None

    route = winner["route"]
    cost = winner["pricing"]["cost_breakdown"]["total"]
    days = route["estimated_days"]
    mode = route["mode"]
    budget = constraints.get("budget_usd")
    deadline = constraints.get("deadline_days")

    # Build reasoning summary
    reason_parts = [
        f"Recommended **{route['name']}** with an overall score of {winner['overall_score']:.1f}/100."
    ]

    if budget and cost <= budget:
        reason_parts.append(f"This route costs ${cost:,.2f}, saving ${budget - cost:,.2f} from the ${budget:,.0f} budget.")
    elif budget:
        reason_parts.append(f"Note: This route costs ${cost:,.2f}, which is ${cost - budget:,.2f} over the ${budget:,.0f} budget.")

    if deadline and days <= deadline:
        reason_parts.append(f"Delivery in {days:.1f} days meets the {deadline}-day deadline with {deadline - days:.1f} days buffer.")
    elif deadline:
        reason_parts.append(f"Delivery in {days:.1f} days exceeds the {deadline}-day deadline.")

    reasoning_summary = " ".join(reason_parts)

    # Build trade-off analysis
    trade_parts = []
    if runner_up:
        ru_route = runner_up["route"]
        ru_cost = runner_up["pricing"]["cost_breakdown"]["total"]
        ru_days = ru_route["estimated_days"]

        cost_diff = cost - ru_cost
        time_diff = days - ru_days

        if cost_diff < 0 and time_diff > 0:
            trade_parts.append(
                f"Chose {mode} over {ru_route['mode']} to save ${abs(cost_diff):,.0f}, "
                f"accepting {abs(time_diff):.1f} extra days of transit."
            )
        elif cost_diff > 0 and time_diff < 0:
            trade_parts.append(
                f"Chose {mode} over {ru_route['mode']} for {abs(time_diff):.1f} faster delivery, "
                f"at an additional cost of ${abs(cost_diff):,.0f}."
            )
        else:
            trade_parts.append(
                f"This route outperforms {ru_route['name']} with a "
                f"score of {winner['overall_score']:.1f} vs {runner_up['overall_score']:.1f}."
            )

    weather_risk = winner.get("weather", {}).get("overall_risk_level", "low")
    if weather_risk in ("high", "severe"):
        trade_parts.append(f"Weather risk is {weather_risk} — consider monitoring conditions before departure.")
    else:
        trade_parts.append(f"Weather conditions are favorable ({weather_risk} risk).")

    congestion = winner.get("congestion", {}).get("overall_congestion", "low")
    if congestion in ("high", "critical"):
        trade_parts.append(f"Port congestion is {congestion} — factor in potential delays.")

    trade_off_analysis = " ".join(trade_parts) if trade_parts else "Optimal route with no significant trade-offs."

    return {
        "reasoning_summary": reasoning_summary,
        "trade_off_analysis": trade_off_analysis
    }


async def decision_node(state: ShipmentState, llm=None) -> Dict[str, Any]:
    """
    Make the final route recommendation with justified reasoning.
    Uses LLM for elegant reasoning, with algorithmic fallback.
    """
    scored_routes = state.get("scored_routes", [])
    constraints = state.get("parsed_constraints", {})
    original_query = state.get("raw_input", "")

    if not scored_routes:
        return {
            "recommendation": None,
            "alternatives": [],
            "reasoning_summary": "No viable routes could be evaluated.",
            "trade_off_analysis": "No trade-off analysis available.",
            "reasoning_trace": [{
                "agent": "Decision",
                "step": "No Decision Possible",
                "detail": "No scored routes available to make a recommendation.",
                "icon": "❌"
            }]
        }

    # Try LLM-powered decision
    decision = None
    if llm is not None:
        try:
            from agent.prompts import DECISION_PROMPT
            prompt = DECISION_PROMPT.format(
                original_query=original_query,
                constraints=json.dumps(constraints, indent=2),
                scored_routes=json.dumps(
                    [{"id": s["route"]["id"], "name": s["route"]["name"],
                      "mode": s["route"]["mode"], "days": s["route"]["estimated_days"],
                      "cost": s["pricing"]["cost_breakdown"]["total"],
                      "overall_score": s["overall_score"],
                      "pros": s["pros"], "cons": s["cons"]}
                     for s in scored_routes],
                    indent=2
                )
            )
            response = await llm.ainvoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
            if json_match:
                decision = json.loads(json_match.group())
        except Exception as e:
            print(f"LLM decision failed, using fallback: {e}")

    # Fallback to algorithmic decision
    if decision is None:
        decision = _algorithmic_decision(scored_routes, constraints, original_query)

    recommendation = scored_routes[0]
    alternatives = scored_routes[1:]

    return {
        "recommendation": recommendation,
        "alternatives": alternatives,
        "reasoning_summary": decision.get("reasoning_summary", "Route recommended based on multi-criteria analysis."),
        "trade_off_analysis": decision.get("trade_off_analysis", "Trade-off analysis not available."),
        "reasoning_trace": [{
            "agent": "Decision",
            "step": f"🏆 Recommended: {recommendation['route']['name']}",
            "detail": (
                f"{decision.get('reasoning_summary', '')}\n\n"
                f"Trade-offs: {decision.get('trade_off_analysis', '')}"
            ),
            "icon": "🏆",
            "data": {
                "recommended_route": recommendation["route"]["id"],
                "overall_score": recommendation["overall_score"],
                "cost": recommendation["pricing"]["cost_breakdown"]["total"],
                "days": recommendation["route"]["estimated_days"],
                "alternatives_count": len(alternatives)
            }
        }]
    }
