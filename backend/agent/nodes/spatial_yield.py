"""
Spatial Yield Optimizer Node.
Uses LLM as a 3D bin-packing heuristic to calculate the true utilization of cargo containers.
"""

import json
import re
from typing import Dict, Any
from agent.state import ShipmentState


def _fallback_spatial(constraints: Dict) -> Dict[str, Any]:
    return {
        "teu_volume": 1.0,
        "utilization_percentage": 50,
        "optimization_warning": "Could not optimize spatial yield. Assuming standard TEU."
    }


async def spatial_yield_node(state: ShipmentState, llm=None) -> Dict[str, Any]:
    """Generates container utilization limits and optimization suggestions."""
    constraints = state.get("parsed_constraints", {})
    cargo_items = constraints.get("cargo_items", [])
    weight = constraints.get("weight_kg", 0)

    spatial_data = None

    if llm is not None and cargo_items:
        try:
            from agent.prompts import SPATIAL_YIELD_PROMPT
            
            prompt = SPATIAL_YIELD_PROMPT.format(
                cargo_items=json.dumps(cargo_items),
                weight=weight
            )
            response = await llm.ainvoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)

            json_match = re.search(r'(\{.*\})', content, re.DOTALL)
            if json_match:
                spatial_data = json.loads(json_match.group(1))
        except Exception as e:
            print(f"Spatial Yield LLM failed: {e}")

    if spatial_data is None:
        spatial_data = _fallback_spatial(constraints)

    utilization = spatial_data.get("utilization_percentage", 50)
    warning = spatial_data.get("optimization_warning", "")

    return {
        "spatial_yield": spatial_data,
        "reasoning_trace": [{
            "agent": "Spatial Yield",
            "step": "Container Optimization Assessed",
            "detail": f"Utilization: {utilization}% | TEUs: {spatial_data.get('teu_volume', 'N/A')}\n{warning}",
            "icon": "📐",
            "data": spatial_data
        }]
    }
