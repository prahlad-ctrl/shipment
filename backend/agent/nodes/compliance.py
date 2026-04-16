"""
Customs & Regulatory Compliance Node.
Applies HS Codes, estimated tariffs, and regulatory flags to the shipment state.
"""

import json
import re
from typing import Dict, Any
from agent.state import ShipmentState


def _fallback_compliance() -> Dict[str, Any]:
    return {
        "hs_code": "9999.99",
        "estimated_tariffs_usd": 0,
        "flagged_regulations": [],
        "required_documents": ["Commercial Invoice", "Packing List"]
    }


async def compliance_node(state: ShipmentState, llm=None) -> Dict[str, Any]:
    """Generates customs and regulatory compliance details based on cargo and route."""
    constraints = state.get("parsed_constraints", {})
    origin = constraints.get("origin", "Unknown")
    destination = constraints.get("destination", "Unknown")
    
    cargo_items = constraints.get("cargo_items", [])
    cargo_material = constraints.get("cargo_type") or "general goods"
    if cargo_items:
        cargo_material += f" ({cargo_items[0].get('type', 'items')})"

    compliance_data = None

    if llm is not None:
        try:
            from agent.prompts import COMPLIANCE_PROMPT
            
            prompt = COMPLIANCE_PROMPT.format(
                origin=origin,
                destination=destination,
                cargo_material=cargo_material
            )
            response = await llm.ainvoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)

            json_match = re.search(r'(\{.*\})', content, re.DOTALL)
            if json_match:
                compliance_data = json.loads(json_match.group(1))
        except Exception as e:
            print(f"Compliance LLM failed: {e}")

    if compliance_data is None:
        compliance_data = _fallback_compliance()

    regulations = compliance_data.get("flagged_regulations", [])
    reg_text = f"Flags: {len(regulations)}" if regulations else "Standard Clearance"

    return {
        "customs_compliance": compliance_data,
        "reasoning_trace": [{
            "agent": "Compliance",
            "step": "Customs & Regulations Checked",
            "detail": f"HS Code: {compliance_data.get('hs_code', 'N/A')} | {reg_text}",
            "icon": "🛂",
            "data": compliance_data
        }]
    }
