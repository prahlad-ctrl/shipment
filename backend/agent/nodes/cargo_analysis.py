"""
Cargo Analysis Agent Node.
Analyzes the shipment request and parsed constraints to deduce cargo fragility and handling limits.
"""

import json
import re
from typing import Dict, Any
from agent.state import ShipmentState


def _fallback_cargo_analysis(constraints: Dict) -> Dict[str, Any]:
    """Fallback logic if LLM is unavailable."""
    cargo_type = constraints.get("cargo_type", "general").lower()
    
    score = 30
    sensitivity = "low"
    instructions = ["Handle with care"]
    
    if cargo_type == "fragile":
        score = 85
        sensitivity = "high"
        instructions = ["Do not double stack", "Fragile cargo, minimize transshipments"]
    elif cargo_type == "perishable":
        score = 60
        sensitivity = "medium"
        instructions = ["Requires temperature control", "Expedite handling"]
    elif cargo_type == "hazardous":
        score = 75
        sensitivity = "medium"
        instructions = ["Hazmat protocols required", "Stow away from heat sources"]

    return {
        "fragility_score": score,
        "vibration_sensitivity": sensitivity,
        "handling_instructions": instructions
    }


async def cargo_analysis_node(state: ShipmentState, llm=None) -> Dict[str, Any]:
    """
    Analyze the raw input and constraints to extract fragility and handling needs.
    """
    query = state.get("raw_input", "")
    constraints = state.get("parsed_constraints", {})

    profile = None

    if llm is not None:
        try:
            from agent.prompts import CARGO_ANALYSIS_PROMPT
            
            prompt = CARGO_ANALYSIS_PROMPT.format(
                query=query,
                parsed_constraints=json.dumps(constraints)
            )
            response = await llm.ainvoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)

            json_match = re.search(r'(\{.*\})', content, re.DOTALL)
            if json_match:
                profile = json.loads(json_match.group(1))
        except Exception as e:
            print(f"Cargo analysis LLM failed: {e}")

    if profile is None:
        profile = _fallback_cargo_analysis(constraints)

    # Validate output
    score = profile.get("fragility_score", 30)
    
    step_detail = f"Fragility Score: {score}/100 | Sensitivity: {profile.get('vibration_sensitivity', 'unknown')}"

    return {
        "cargo_profile": profile,
        "reasoning_trace": [{
            "agent": "Analysis",
            "step": "Cargo Fragility Assessed",
            "detail": step_detail,
            "icon": "📦",
            "data": profile
        }]
    }
