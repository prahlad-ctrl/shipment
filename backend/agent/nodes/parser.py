"""
Parser Agent Node.
Extracts structured constraints from natural language shipment requests.
Uses LLM for NLP parsing with fallback to regex-based extraction.
"""

import json
import re
from typing import Dict, Any
from agent.state import ShipmentState


def _fallback_parse(query: str) -> Dict[str, Any]:
    """
    Regex-based fallback parser when LLM is unavailable.
    Handles common patterns like "Ship 500kg from Dubai to Rotterdam within 5 days under $4000"
    """
    result = {
        "origin": None,
        "destination": None,
        "weight_kg": None,
        "deadline_days": None,
        "budget_usd": None,
        "priority": "balanced",
        "cargo_type": "general",
        "cargo_items": [],
        "special_requirements": []
    }

    # Extract cargo items explicitly (e.g. "120 cartons of textiles (0.5x0.4x0.4 meters each)")
    cargo_item_pattern = re.finditer(r'(\d+)\s+([a-zA-Z]+)\s+of\s+([a-zA-Z\s]+)\s*\(([\d\.]+)\s*[xX]\s*([\d\.]+)\s*[xX]\s*([\d\.]+)', query, re.IGNORECASE)
    for match in cargo_item_pattern:
        qty = int(match.group(1))
        container_type = match.group(3).strip()
        l = float(match.group(4))
        w = float(match.group(5))
        h = float(match.group(6))
        
        result["cargo_items"].append({
            "type": container_type,
            "qty": qty,
            "dim": [l, w, h]
        })

    # Extract weight
    weight_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:kg|kilos?|kilograms?)', query, re.IGNORECASE)
    if weight_match:
        result["weight_kg"] = float(weight_match.group(1))
    else:
        tons_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:tons?|tonnes?)', query, re.IGNORECASE)
        if tons_match:
            result["weight_kg"] = float(tons_match.group(1)) * 1000
        else:
            lbs_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:lbs?|pounds?)', query, re.IGNORECASE)
            if lbs_match:
                result["weight_kg"] = float(lbs_match.group(1)) * 0.4536

    # Extract from/to
    from_to = re.search(r'from\s+([^,]+?)\s+to\s+([^,]+?)(?:\s+within|\s+in|\s+under|\s+by|\s+before|$|,|\.)', query, re.IGNORECASE)
    if from_to:
        result["origin"] = from_to.group(1).strip()
        result["destination"] = from_to.group(2).strip()

    # Extract deadline
    deadline_match = re.search(r'(?:within|in|under)\s+(\d+)\s*(?:days?|d\b)', query, re.IGNORECASE)
    if deadline_match:
        result["deadline_days"] = int(deadline_match.group(1))

    # Extract budget (look for $ sign specifically)
    budget_match = re.search(r'\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?)', query, re.IGNORECASE)
    if budget_match:
        result["budget_usd"] = float(budget_match.group(1).replace(",", ""))
    else:
        # Try "budget X" or "under X dollars" patterns without $
        budget_match2 = re.search(r'(?:budget|under|below|max(?:imum)?)\s+(\d{3,})\s*(?:usd|dollars?|bucks)?', query, re.IGNORECASE)
        if budget_match2:
            result["budget_usd"] = float(budget_match2.group(1).replace(",", ""))

    # Infer priority
    query_lower = query.lower()
    if any(w in query_lower for w in ["cheap", "budget", "cost", "affordable", "economical"]):
        result["priority"] = "cost"
    elif any(w in query_lower for w in ["fast", "urgent", "express", "rush", "asap", "quick"]):
        result["priority"] = "speed"
    elif any(w in query_lower for w in ["reliable", "safe", "secure", "guaranteed"]):
        result["priority"] = "reliability"

    # Cargo type
    if any(w in query_lower for w in ["perishable", "food", "fresh", "frozen"]):
        result["cargo_type"] = "perishable"
    elif any(w in query_lower for w in ["hazardous", "dangerous", "chemical"]):
        result["cargo_type"] = "hazardous"
    elif any(w in query_lower for w in ["fragile", "glass", "delicate"]):
        result["cargo_type"] = "fragile"

    return result


async def parser_node(state: ShipmentState, llm=None) -> Dict[str, Any]:
    """
    Parse natural language shipment request into structured constraints.
    Uses LLM if available, with regex fallback.
    """
    query = state["raw_input"]

    parsed = None

    # Try LLM parsing first
    if llm is not None:
        try:
            from agent.prompts import PARSER_PROMPT
            
            chat_history = state.get("chat_history", [])
            current_constraints = state.get("parsed_constraints", {})
            target_lang = state.get("target_language", "English")
            
            prompt = PARSER_PROMPT.format(
                query=query,
                chat_history=json.dumps(chat_history) if chat_history else "None",
                current_constraints=json.dumps(current_constraints) if current_constraints else "None",
                target_language=target_lang
            )
            response = await llm.ainvoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)

            # Extract JSON from response (support nested objects and arrays)
            json_match = re.search(r'(\{.*\})', content, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(1))
        except Exception as e:
            print(f"LLM parsing failed, using fallback: {e}")

    # Fallback to regex
    if parsed is None:
        parsed = _fallback_parse(query)

    # Validate required fields
    if not parsed.get("origin") or not parsed.get("destination"):
        return {
            "parsed_constraints": parsed,
            "reasoning_trace": [{
                "agent": "Parser",
                "step": "Parsing Failed",
                "detail": f"Could not extract origin/destination from: '{query}'",
                "icon": "❌"
            }],
            "error": "Could not parse origin and destination from the request."
        }

    return {
        "parsed_constraints": parsed,
        "reasoning_trace": [{
            "agent": "Parser",
            "step": "Request Parsed",
            "detail": (
                f"Extracted: {parsed['origin']} → {parsed['destination']}, "
                f"{parsed.get('weight_kg', 'N/A')}kg, "
                f"Deadline: {parsed.get('deadline_days', 'None')} days, "
                f"Budget: ${parsed.get('budget_usd', 'None')}, "
                f"Priority: {parsed.get('priority', 'balanced')}"
            ),
            "icon": "🔍",
            "data": parsed
        }]
    }
