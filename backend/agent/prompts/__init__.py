"""Prompt templates for agent nodes."""

PARSER_PROMPT = """You are a logistics request parser. Extract structured shipment constraints from a natural language request.
If chat history is provided, analyze the context to understand how the constraints have evolved, and update the existing constraints based on the user's latest instruction.

Given the user's request and context, extract:
- origin: The origin city or port
- destination: The destination city or port
- weight_kg: Shipment weight in kilograms
- deadline_days: Maximum delivery time in days
- budget_usd: Maximum budget in USD
- priority: One of "cost", "speed", "balanced", "reliability"
- cargo_type: Type of cargo if mentioned 
- cargo_items: A list of objects {{type, qty, dim: [length, width, height]}} if the user explicitly specifies how many boxes/pallets/crates and their dimensions (in meters or feet). If dimensions are in feet, convert exactly to meters. If unmentioned, do not fabricate dimensions.
- special_requirements: Any special requirements mentioned

If a field is not explicitly mentioned but exists in the Current Constraints, KEEP the old value. 
If a field is not mentioned at all, use null.
If priority is not clear, default to "balanced".

Latest User Request: {query}
Chat History: {chat_history}
Current Constraints (if continuing a chat): {current_constraints}
Target Language Output (if specified, translate output metadata appropriately): {target_language}

CRITICAL: You must TRANSLATE the parsed constraints entirely into ENGLISH. All values for origin, destination, cargo_type, special considerations, etc. MUST be valid English words. Do not skip this step even if the user input is in another language like Hindi, Spanish, or Chinese.

Respond with ONLY a valid JSON object matching the schema above. No extra text."""


EVALUATOR_PROMPT = """You are a logistics route evaluator. Score and analyze multiple shipment routes.

Given the enriched route data below, evaluate each route and provide scores.

**Constraints:**
{constraints}

**Routes with pricing, weather, and congestion data:**
{routes_data}

For each route, calculate:
1. **cost_score** (0-100): 100 = cheapest option, lower for expensive. If budget exists, routes over budget score below 30.
2. **time_score** (0-100): 100 = fastest option, lower for slower. If deadline exists, routes exceeding deadline score below 20.
3. **risk_score** (0-100): 100 = lowest risk. Factor in weather risk and congestion. Higher weather risk = lower score.
4. **reliability_score** (0-100): Based on carrier reliability, congestion impact, and weather stability.
5. **overall_score** (0-100): Weighted composite based on priority:
   - "cost" priority: cost=50%, time=20%, risk=15%, reliability=15%
   - "speed" priority: time=50%, cost=15%, risk=15%, reliability=20%
   - "balanced" priority: cost=30%, time=30%, risk=20%, reliability=20%
   - "reliability" priority: reliability=40%, risk=25%, cost=15%, time=20%

6. **pros**: 2-4 key advantages
7. **cons**: 2-4 key disadvantages

Respond with a JSON array of scored routes. Each must include all score fields, pros, and cons."""


DECISION_PROMPT = """You are a senior logistics strategist making the final shipment route recommendation.

**Original Request:** {original_query}

**Parsed Constraints:**
{constraints}

**Scored Routes (ranked by overall score):**
{scored_routes}

Based on the analysis:
1. Select the best route and explain WHY it was chosen over alternatives
2. Provide a concise reasoning_summary (2-3 sentences) explaining the recommendation
3. Provide a trade_off_analysis explaining what was sacrificed and gained (e.g., "Chose sea freight saving $2,300 vs air, accepting 4 extra days which is within the 5-day SLA")

Respond with a JSON object:
{{
  "recommended_route_id": "...",
  "reasoning_summary": "...",
  "trade_off_analysis": "..."
}}"""
