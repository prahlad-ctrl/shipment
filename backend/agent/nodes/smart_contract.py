"""
Autonomous Smart Contract Generator Node.
Generates Solidity logic mapping to the recommended route waypoints.
"""

import json
import re
from typing import Dict, Any
from agent.state import ShipmentState


def _fallback_contract(route_id: str) -> Dict[str, Any]:
    return {
        "solidity_code": "// Processing Escrow Smart Contract...\n// LLM Generation Failed. Using Standard Template.\ncontract ShipmentEscrow {\n    function releaseFunds() public {\n        // Default release\n    }\n}",
        "milestones": ["100% on Arrival"]
    }


async def smart_contract_node(state: ShipmentState, llm=None) -> Dict[str, Any]:
    """Generates the smart contract from the decided route."""
    recommendation = state.get("recommendation")
    
    contract_data = None

    if recommendation and llm is not None:
        try:
            from agent.prompts import SMART_CONTRACT_PROMPT
            
            route = recommendation.get("route", {})
            cost = recommendation.get("adjusted_cost", 0)
            
            # Formulate route details string
            hubs = route.get("hubs", [])
            route_details = ", ".join(hubs) if hubs else "Direct Route"
            
            prompt = SMART_CONTRACT_PROMPT.format(
                route_id=route.get("id", "Unknown"),
                cost=cost,
                route_details=route_details
            )
            response = await llm.ainvoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)

            json_match = re.search(r'(\{.*\})', content, re.DOTALL)
            if json_match:
                contract_data = json.loads(json_match.group(1))
        except Exception as e:
            print(f"Smart Contract LLM failed: {e}")

    if contract_data is None:
        route_id = recommendation.get("route", {}).get("id", "Unknown") if recommendation else "N/A"
        contract_data = _fallback_contract(route_id)

    num_milestones = len(contract_data.get("milestones", []))

    return {
        "smart_contract": contract_data,
        "reasoning_trace": [{
            "agent": "Smart Contract",
            "step": "Escrow Logic Compiled",
            "detail": f"Generated Solidity Contract with {num_milestones} execution milestones.",
            "icon": "⛓️",
            "data": contract_data
        }]
    }
