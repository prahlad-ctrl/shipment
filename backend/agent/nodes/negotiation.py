"""
Negotiation Agent Node.
Simulates a brokerage negotiation with the carrier to secure a volume discount.
"""

from typing import Dict, Any
import random
from langchain_core.messages import SystemMessage, HumanMessage

from agent.state import ShipmentState

async def negotiation_node(state: ShipmentState, llm) -> Dict[str, Any]:
    """Simulate a negotiation for the top route."""
    scored_routes = state.get("scored_routes", [])
    if not scored_routes:
        return {}

    # Get the top recommended route
    top_route = max(scored_routes, key=lambda x: x["overall_score"])
    carrier = top_route["pricing"]["cost_breakdown"]["carrier_name"]
    original_cost = top_route["pricing"]["cost_breakdown"]["total"]
    
    trace_step = {
        "agent": "Broker Agent",
        "step": f"Negotiating with {carrier}",
        "detail": f"Initiating negotiation sequence to reduce the ${original_cost:,.2f} quote.",
        "icon": "🤝"
    }
    
    # Generate the log and discount
    discount = random.uniform(0.05, 0.12)
    new_cost = original_cost * (1 - discount)
    
    # We will adjust the route object heavily by reference, but we must be careful with LangGraph state.
    # Usually returning the updated array is best, but modifying in place here works since it's a deep object.
    
    # Let's save the original cost for the frontend to show the "crossed out" price
    top_route["pricing"]["cost_breakdown"]["original_total"] = original_cost
    top_route["pricing"]["cost_breakdown"]["total"] = new_cost
    top_route["pricing"]["cost_breakdown"]["freight"] *= (1 - discount)
    
    if not llm:
        log = [
            {"sender": "You", "message": f"Hello {carrier}, we have a firm shipment ready to book. Your quote is ${original_cost:,.2f}, which is slightly above budget. Can we get a spot discount?"},
            {"sender": "Carrier", "message": f"We can offer a {(discount*100):.1f}% reduction if you book today. New total: ${new_cost:,.2f}."},
            {"sender": "You", "message": "Deal. Booking confirmed."}
        ]
        
        trace_step["detail"] = f"Algorithmic negotiation succeeded. New quote: ${new_cost:,.2f}."
        return {
            "negotiation_log": log,
            "reasoning_trace": [trace_step]
        }

    # Use LLM
    prompt = f"""You are an AI Freight Broker negotiating with {carrier}. 
The original quote for this shipment is ${original_cost:,.2f}. 
Write a short, realistic 3-message negotiation transcript (You, Carrier, You).
The Carrier should agree to a discount bringing the cost to ${new_cost:,.2f}.
Return your output ONLY as a JSON list of objects with 'sender' and 'message' keys.
Example:
[
  {{"sender": "You", "message": "Hi, we need to lower the price..."}},
  {{"sender": "Carrier", "message": "We can offer a discount bringing it to $X"}},
  {{"sender": "You", "message": "Great, booked."}}
]
"""
    
    try:
        response = await llm.ainvoke([SystemMessage(content="You are a JSON-only API that outputs negotiation logs."), HumanMessage(content=prompt)])
        
        import json
        import re
        
        content = response.content
        match = re.search(r'\[.*\]', content, re.DOTALL)
        if match:
            log = json.loads(match.group(0))
        else:
            log = json.loads(content)
            
        trace_step["detail"] = f"Successfully negotiated a discount using LLM. New quote: ${new_cost:,.2f}."
        
        return {
            "negotiation_log": log,
            "reasoning_trace": [trace_step]
        }
    except Exception as e:
        print(f"[Negotiation] failed: {e}")
        log = [
            {"sender": "You", "message": f"Hello {carrier}, can we get a discount on ${original_cost:,.2f}?"},
            {"sender": "Carrier", "message": f"Yes, we can drop it to ${new_cost:,.2f}."},
            {"sender": "You", "message": "Deal."}
        ]
        return {
            "negotiation_log": log,
            "reasoning_trace": [{**trace_step, "detail": "Negotiation utilized fallback. Rate updated.", "icon": "🤝"}]
        }
