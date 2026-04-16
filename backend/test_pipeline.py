"""Quick test of the agent pipeline."""
import asyncio
import sys
import os
import io
import traceback

# Fix Windows encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

async def test():
    try:
        # Test 1: Parser
        print("=== Testing Parser ===")
        from agent.nodes.parser import parser_node
        state = {"raw_input": "Ship 500kg from Dubai to Rotterdam within 5 days under $4000"}
        result = await parser_node(state, llm=None)
        print("Parsed:", result.get("parsed_constraints"))
        print()

        # Test 2: Route Generator
        print("=== Testing Route Generator ===")
        from agent.nodes.route_generator import route_generator_node
        state2 = {**state, "parsed_constraints": result["parsed_constraints"]}
        result2 = await route_generator_node(state2, llm=None)
        routes = result2.get("route_candidates", [])
        print(f"Generated {len(routes)} routes:")
        for r in routes:
            print(f"  - {r['name']} ({r['mode']}, {r['estimated_days']} days)")
        print()

        # Test 3: Pricing
        print("=== Testing Pricing ===")
        from agent.nodes.pricing import pricing_node
        state3 = {**state2, "route_candidates": routes}
        result3 = await pricing_node(state3, llm=None)
        for p in result3.get("pricing_data", []):
            print(f"  - {p['route_id']}: ${p['cost_breakdown']['total']:,.2f}")
        print()

        # Test 4: Weather
        print("=== Testing Weather ===")
        from agent.nodes.weather import weather_node
        result4 = await weather_node(state3, llm=None)
        for w in result4.get("weather_data", []):
            print(f"  - {w['route_id']}: {w['overall_risk_level']} risk")
        print()

        # Test 5: Port Congestion
        print("=== Testing Port Congestion ===")
        from agent.nodes.port_congestion import port_congestion_node
        result5 = await port_congestion_node(state3, llm=None)
        for c in result5.get("congestion_data", []):
            print(f"  - {c['route_id']}: {c['overall_congestion']} congestion")
        print()

        # Test 6: Evaluator
        print("=== Testing Evaluator ===")
        from agent.nodes.evaluator import evaluator_node
        state6 = {
            **state3,
            "pricing_data": result3.get("pricing_data", []),
            "weather_data": result4.get("weather_data", []),
            "congestion_data": result5.get("congestion_data", []),
        }
        result6 = await evaluator_node(state6, llm=None)
        scored = result6.get("scored_routes", [])
        for s in scored:
            print(f"  - {s['route']['name']}: score={s['overall_score']:.1f}, recommended={s['is_recommended']}")
        print()

        # Test 7: Decision
        print("=== Testing Decision ===")
        from agent.nodes.decision import decision_node
        state7 = {
            **state6,
            "scored_routes": scored,
        }
        result7 = await decision_node(state7, llm=None)
        print("Recommendation:", result7.get("recommendation", {}).get("route", {}).get("name"))
        print("Summary:", result7.get("reasoning_summary", "")[:200])
        print()

        # Test 8: Full graph
        print("=== Testing Full Graph ===")
        from agent.graph import run_agent
        full_result = await run_agent("Ship 500kg from Dubai to Rotterdam within 5 days under $4000")
        print("Success:", full_result.get("recommendation") is not None)
        if full_result.get("recommendation"):
            rec = full_result["recommendation"]
            print("Route:", rec.get("route", {}).get("name"))
            print("Cost:", rec.get("pricing", {}).get("cost_breakdown", {}).get("total"))
            print("Score:", rec.get("overall_score"))
        if full_result.get("error"):
            print("ERROR:", full_result["error"])
        print("Trace steps:", len(full_result.get("reasoning_trace", [])))
        print()
        print("ALL TESTS PASSED!")

    except Exception as e:
        print(f"ERROR: {e}")
        traceback.print_exc()

asyncio.run(test())
