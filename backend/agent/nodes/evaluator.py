"""
Evaluator Agent Node.
Scores all enriched routes using multi-criteria analysis.
Uses LLM for nuanced evaluation with algorithmic fallback.
Now includes sustainability and risk scenario factors.
"""

import json
import re
from typing import Dict, Any, List
from agent.state import ShipmentState


def _algorithmic_scoring(
    route: Dict,
    pricing: Dict,
    weather: Dict,
    congestion: Dict,
    sustainability: Dict,
    risk_penalty: Dict,
    constraints: Dict,
    all_prices: List[float],
    cargo_profile: Dict
) -> Dict[str, Any]:
    """
    Deterministic multi-criteria scoring when LLM is not available.
    Now includes sustainability and risk scenario adjustments.
    """
    budget = constraints.get("budget_usd")
    deadline = constraints.get("deadline_days")
    priority = constraints.get("priority", "balanced")

    cost = pricing["cost_breakdown"]["total"]
    days = route["estimated_days"]
    weather_risk = weather.get("overall_risk_score", 0.1)
    congestion_score = congestion.get("overall_score", 0.2)
    green_score = sustainability.get("green_score", 50)

    # ── Apply risk scenario penalties ──
    time_penalty = risk_penalty.get("time_penalty_days", 0)
    cost_penalty = risk_penalty.get("cost_penalty_usd", 0)
    weather_risk_increase = risk_penalty.get("weather_risk_increase", 0)

    adjusted_cost = cost + cost_penalty
    adjusted_days = days + time_penalty
    adjusted_weather_risk = min(1.0, weather_risk + weather_risk_increase)

    # ── Cost Score (0-100) ──
    if all_prices:
        min_price = min(all_prices)
        max_price = max(all_prices)
        price_range = max_price - min_price if max_price > min_price else 1
        cost_score = max(0, 100 - ((adjusted_cost - min_price) / price_range) * 70)
    else:
        cost_score = 50

    if budget and adjusted_cost > budget:
        cost_score = max(0, cost_score * 0.3)  # Severe penalty for over budget
    elif budget and adjusted_cost <= budget * 0.7:
        cost_score = min(100, cost_score + 15)  # Bonus for well under budget

    # ── Time Score (0-100) ──
    if deadline:
        if adjusted_days <= deadline:
            time_score = min(100, 60 + (deadline - adjusted_days) / deadline * 40)
        else:
            time_score = max(0, 30 - (adjusted_days - deadline) * 10)
    else:
        # Score based on speed (faster = higher)
        time_score = max(10, 100 - adjusted_days * 5)

    # ── Risk Score (0-100, higher = safer) ──
    risk_score = max(0, 100 - adjusted_weather_risk * 100)
    # Add congestion penalty
    risk_score = max(0, risk_score - congestion_score * 30)
    # Risk scenario penalty
    if time_penalty > 0:
        risk_score = max(0, risk_score - 10)

    # ── Reliability Score (0-100) ──
    reliability_score = 80  # base
    if adjusted_weather_risk > 0.5:
        reliability_score -= 20
    if congestion_score > 0.5:
        reliability_score -= 15
    if route["mode"] == "air":
        reliability_score += 5
    elif route["mode"] == "sea":
        reliability_score -= 5
    if time_penalty > 0:
        reliability_score -= 10  # Risk scenarios reduce reliability
        
    fragility = cargo_profile.get("fragility_score", 0) if cargo_profile else 0
    if fragility > 70:
        if route["mode"] == "sea":
            reliability_score -= 25 # High risk of cargo damage at sea
        elif route["mode"] == "multimodal":
            reliability_score -= 20 # High handling breakage risk
        else:
            reliability_score += 10 # Safer handling on direct air/road
            
    reliability_score = max(10, min(100, reliability_score))

    # ── Overall Score ──
    weights = {
        "cost": {"cost": 0.50, "time": 0.20, "risk": 0.15, "reliability": 0.15},
        "speed": {"cost": 0.15, "time": 0.50, "risk": 0.15, "reliability": 0.20},
        "balanced": {"cost": 0.30, "time": 0.30, "risk": 0.20, "reliability": 0.20},
        "reliability": {"cost": 0.15, "time": 0.20, "risk": 0.25, "reliability": 0.40}
    }
    w = weights.get(priority, weights["balanced"])
    overall = (
        w["cost"] * cost_score +
        w["time"] * time_score +
        w["risk"] * risk_score +
        w["reliability"] * reliability_score
    )

    # ── Pros & Cons ──
    pros = []
    cons = []

    if cost_score >= 70:
        pros.append(f"Cost-effective at ${adjusted_cost:,.0f}")
    elif cost_score < 40:
        cons.append(f"Expensive at ${adjusted_cost:,.0f}")

    if budget and adjusted_cost <= budget:
        pros.append(f"Within ${budget:,.0f} budget (saves ${budget - adjusted_cost:,.0f})")
    elif budget and adjusted_cost > budget:
        cons.append(f"Exceeds ${budget:,.0f} budget by ${adjusted_cost - budget:,.0f}")

    if deadline and adjusted_days <= deadline:
        pros.append(f"Meets {deadline}-day deadline ({adjusted_days:.1f} days)")
    elif deadline and adjusted_days > deadline:
        cons.append(f"Misses {deadline}-day deadline by {adjusted_days - deadline:.1f} days")

    if adjusted_days <= 2:
        pros.append("Ultra-fast delivery")
    elif adjusted_days >= 10:
        cons.append(f"Long transit time ({adjusted_days:.0f} days)")

    if adjusted_weather_risk < 0.3:
        pros.append("Low weather risk")
    elif adjusted_weather_risk > 0.6:
        cons.append(f"High weather risk ({weather.get('overall_risk_level', 'unknown')})")

    if congestion_score < 0.3:
        pros.append("Low port congestion")
    elif congestion_score > 0.5:
        cons.append(f"Port congestion at {congestion.get('bottleneck_port', 'waypoint')}")

    # Sustainability pros/cons
    if green_score >= 80:
        pros.append(f"Eco-friendly ({sustainability.get('eco_label', 'Excellent')})")
    elif green_score < 35:
        cons.append(f"High carbon footprint ({sustainability.get('total_emissions_kg', 0)} kg CO2e)")
        
    # Fragility pros/cons
    if fragility > 70:
        if route["mode"] in ["sea", "multimodal"]:
            cons.append("High risk of damage for fragile goods")
        elif route["mode"] in ["air", "road"]:
            pros.append("Safer direct handling for fragile goods")

    # Risk scenario cons
    if time_penalty > 0:
        cons.append(
            f"World event penalty: +{time_penalty} days, +${cost_penalty:,.0f} "
            f"({'; '.join(risk_penalty.get('descriptions', []))})"
        )

    return {
        "cost_score": round(cost_score, 1),
        "time_score": round(time_score, 1),
        "risk_score": round(risk_score, 1),
        "reliability_score": round(reliability_score, 1),
        "overall_score": round(overall, 1),
        "green_score": round(green_score, 1),
        "adjusted_cost": round(adjusted_cost, 2),
        "adjusted_days": round(adjusted_days, 1),
        "pros": pros[:5],
        "cons": cons[:5]
    }


async def evaluator_node(state: ShipmentState, llm=None) -> Dict[str, Any]:
    """
    Score all enriched routes using multi-criteria analysis.
    """
    routes = state.get("route_candidates", [])
    pricing_data = state.get("pricing_data", [])
    weather_data = state.get("weather_data", [])
    congestion_data = state.get("congestion_data", [])
    sustainability_data = state.get("sustainability_data", [])
    risk_scenario = state.get("risk_scenario", {})
    constraints = state.get("parsed_constraints", {})
    cargo_profile = state.get("cargo_profile", {})

    if not routes:
        return {
            "scored_routes": [],
            "reasoning_trace": [{
                "agent": "Evaluator",
                "step": "No Routes to Evaluate",
                "detail": "No enriched route data available",
                "icon": "⚖️"
            }]
        }

    # Build lookup maps
    pricing_map = {p["route_id"]: p for p in pricing_data}
    weather_map = {w["route_id"]: w for w in weather_data}
    congestion_map = {c["route_id"]: c for c in congestion_data}
    sustainability_map = {s["route_id"]: s for s in sustainability_data}
    risk_penalties = risk_scenario.get("penalties", {}) if risk_scenario else {}
    all_prices = [p["cost_breakdown"]["total"] for p in pricing_data]

    scored = []
    for route in routes:
        rid = route["id"]
        pricing = pricing_map.get(rid, {"cost_breakdown": {"total": 9999}, "within_budget": None, "budget_delta": None})
        weather = weather_map.get(rid, {"overall_risk_level": "low", "overall_risk_score": 0.1})
        congestion = congestion_map.get(rid, {"overall_congestion": "low", "overall_score": 0.1})
        sustainability = sustainability_map.get(rid, {"green_score": 50, "total_emissions_kg": 0, "eco_label": "Unknown"})
        risk_penalty = risk_penalties.get(rid, {})

        scores = _algorithmic_scoring(
            route, pricing, weather, congestion, sustainability, risk_penalty,
            constraints, all_prices, cargo_profile
        )

        scored.append({
            "route": route,
            "pricing": pricing,
            "weather": weather,
            "congestion": congestion,
            "sustainability": sustainability,
            **scores,
            "is_recommended": False
        })

    # Sort by overall score (descending)
    scored.sort(key=lambda x: x["overall_score"], reverse=True)

    # Mark winner
    if scored:
        scored[0]["is_recommended"] = True

    # Build reasoning
    ranking = "\n".join(
        f"  {'🏆' if s['is_recommended'] else '  '} #{i+1} {s['route']['name']}: "
        f"Score={s['overall_score']:.1f} (Cost={s['cost_score']:.0f}, Time={s['time_score']:.0f}, "
        f"Risk={s['risk_score']:.0f}, Reliability={s['reliability_score']:.0f}, "
        f"Green={s['green_score']:.0f})"
        for i, s in enumerate(scored)
    )

    return {
        "scored_routes": scored,
        "reasoning_trace": [{
            "agent": "Evaluator",
            "step": f"Routes Scored — Winner: {scored[0]['route']['name'] if scored else 'None'}",
            "detail": f"Ranking (priority: {constraints.get('priority', 'balanced')}):\n{ranking}",
            "icon": "⚖️",
            "data": {
                "winner": scored[0]["route"]["id"] if scored else None,
                "top_score": scored[0]["overall_score"] if scored else 0
            }
        }]
    }
