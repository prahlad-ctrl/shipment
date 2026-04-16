"""
LangGraph orchestration graph for the Shipment Orchestration Agent.
Defines the multi-agent pipeline with parallel execution for
pricing, weather, port congestion, and sustainability agents.

Pipeline:
  Parser → Hub Resolver → (check) → Route Generator →
  Risk Scenario → Parallel(Pricing, Weather, Congestion, Sustainability) →
  Evaluator → Decision
"""

import os
import asyncio
from typing import Dict, Any, Optional, AsyncGenerator
from dotenv import load_dotenv

from langgraph.graph import StateGraph, END

from agent.state import ShipmentState
from agent.nodes.parser import parser_node
from agent.nodes.hub_resolver import hub_resolver_node
from agent.nodes.route_generator import route_generator_node
from agent.nodes.risk_scenario import risk_scenario_node
from agent.nodes.pricing import pricing_node
from agent.nodes.weather import weather_node
from agent.nodes.port_congestion import port_congestion_node
from agent.nodes.sustainability import sustainability_node
from agent.nodes.evaluator import evaluator_node
from agent.nodes.decision import decision_node

load_dotenv()


def _get_llm():
    """
    Get LLM instance with OpenAI primary, Gemini secondary, Ollama fallback.
    Returns None if none is available (algorithmic mode).
    """
    # Try OpenAI first
    openai_key = os.getenv("OPENAI_API_KEY", "")
    if openai_key and openai_key != "your_openai_api_key_here":
        try:
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                openai_api_key=openai_key,
                temperature=0.1,
                max_tokens=2048
            )
            print("[OK] Using OpenAI LLM")
            return llm
        except Exception as e:
            print(f"[WARN] OpenAI init failed: {e}")

    # Try Google Gemini
    google_key = os.getenv("GOOGLE_API_KEY", "")
    if google_key and google_key != "your_gemini_api_key_here":
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                google_api_key=google_key,
                temperature=0.1,
                max_output_tokens=2048
            )
            print("[OK] Using Google Gemini LLM")
            return llm
        except Exception as e:
            print(f"[WARN] Gemini init failed: {e}")

    # Fallback to Ollama
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3:8b")
    try:
        from langchain_community.chat_models import ChatOllama
        llm = ChatOllama(
            model=ollama_model,
            base_url=ollama_url,
            temperature=0.1
        )
        print(f"[OK] Using Ollama LLM ({ollama_model})")
        return llm
    except Exception as e:
        print(f"[WARN] Ollama init failed: {e}")

    print("[WARN] No LLM available -- running in algorithmic-only mode")
    return None


# Global LLM instance
_llm = None


def get_llm():
    global _llm
    if _llm is None:
        _llm = _get_llm()
    return _llm


# ── Node Wrappers (inject LLM dependency) ───────────────────────────────────

async def _parser(state: ShipmentState) -> Dict[str, Any]:
    return await parser_node(state, llm=get_llm())

async def _hub_resolver(state: ShipmentState) -> Dict[str, Any]:
    return await hub_resolver_node(state, llm=get_llm())

async def _route_generator(state: ShipmentState) -> Dict[str, Any]:
    return await route_generator_node(state, llm=get_llm())

async def _risk_scenario(state: ShipmentState) -> Dict[str, Any]:
    return await risk_scenario_node(state, llm=get_llm())

async def _pricing(state: ShipmentState) -> Dict[str, Any]:
    return await pricing_node(state, llm=get_llm())

async def _weather(state: ShipmentState) -> Dict[str, Any]:
    return await weather_node(state, llm=get_llm())

async def _port_congestion(state: ShipmentState) -> Dict[str, Any]:
    return await port_congestion_node(state, llm=get_llm())

async def _sustainability(state: ShipmentState) -> Dict[str, Any]:
    return await sustainability_node(state, llm=get_llm())

async def _evaluator(state: ShipmentState) -> Dict[str, Any]:
    return await evaluator_node(state, llm=get_llm())

async def _decision(state: ShipmentState) -> Dict[str, Any]:
    return await decision_node(state, llm=get_llm())


# ── Parallel enrichment node ────────────────────────────────────────────────

async def _parallel_enrichment(state: ShipmentState) -> Dict[str, Any]:
    """Run pricing, weather, port congestion, and sustainability checks in parallel."""
    pricing_task = asyncio.create_task(_pricing(state))
    weather_task = asyncio.create_task(_weather(state))
    congestion_task = asyncio.create_task(_port_congestion(state))
    sustainability_task = asyncio.create_task(_sustainability(state))

    pricing_result, weather_result, congestion_result, sustainability_result = await asyncio.gather(
        pricing_task, weather_task, congestion_task, sustainability_task
    )

    # Merge results
    merged = {
        "pricing_data": pricing_result.get("pricing_data", []),
        "weather_data": weather_result.get("weather_data", []),
        "congestion_data": congestion_result.get("congestion_data", []),
        "sustainability_data": sustainability_result.get("sustainability_data", []),
        "reasoning_trace": (
            pricing_result.get("reasoning_trace", []) +
            weather_result.get("reasoning_trace", []) +
            congestion_result.get("reasoning_trace", []) +
            sustainability_result.get("reasoning_trace", [])
        )
    }
    return merged


# ── Error check edge ────────────────────────────────────────────────────────

def _should_continue(state: ShipmentState) -> str:
    """Check if we should continue or abort due to errors."""
    if state.get("error"):
        return "abort"
    return "continue"


def _abort_node(state: ShipmentState) -> Dict[str, Any]:
    """Handle pipeline aborts."""
    return {
        "reasoning_trace": [{
            "agent": "System",
            "step": "Pipeline Aborted",
            "detail": f"Error: {state.get('error', 'Unknown error')}",
            "icon": "❌"
        }]
    }


# ── Build the Graph ─────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    """
    Build and compile the LangGraph agent orchestration graph.

    Pipeline:
    Parser → Hub Resolver → (check) → Route Generator →
    Risk Scenario → Parallel(Pricing, Weather, Congestion, Sustainability) →
    Evaluator → Decision
    """
    graph = StateGraph(ShipmentState)

    # Add nodes
    graph.add_node("parser", _parser)
    graph.add_node("hub_resolver", _hub_resolver)
    graph.add_node("route_generator", _route_generator)
    graph.add_node("risk_scenario", _risk_scenario)
    graph.add_node("enrichment", _parallel_enrichment)
    graph.add_node("evaluator", _evaluator)
    graph.add_node("decision", _decision)
    graph.add_node("abort", _abort_node)

    # Set entry point
    graph.set_entry_point("parser")

    # Parser → Hub Resolver
    graph.add_edge("parser", "hub_resolver")

    # Conditional edge after hub resolver
    graph.add_conditional_edges(
        "hub_resolver",
        _should_continue,
        {"continue": "route_generator", "abort": "abort"}
    )

    # Linear flow
    graph.add_edge("route_generator", "risk_scenario")
    graph.add_edge("risk_scenario", "enrichment")
    graph.add_edge("enrichment", "evaluator")
    graph.add_edge("evaluator", "decision")
    graph.add_edge("decision", END)
    graph.add_edge("abort", END)

    return graph.compile()


# ── Execution helpers ────────────────────────────────────────────────────────

async def run_agent(query: str, world_event: str = "normal") -> Dict[str, Any]:
    """
    Run the full agent pipeline synchronously and return the final state.
    """
    graph = build_graph()

    initial_state: ShipmentState = {
        "raw_input": query,
        "world_event": world_event,
        "parsed_constraints": None,
        "resolved_hubs": None,
        "risk_scenario": None,
        "route_candidates": None,
        "pricing_data": None,
        "weather_data": None,
        "congestion_data": None,
        "sustainability_data": None,
        "scored_routes": None,
        "recommendation": None,
        "alternatives": None,
        "reasoning_summary": None,
        "trade_off_analysis": None,
        "reasoning_trace": [],
        "error": None
    }

    result = await graph.ainvoke(initial_state)
    return result


async def run_agent_streaming(query: str, world_event: str = "normal") -> AsyncGenerator[Dict[str, Any], None]:
    """
    Run the agent pipeline with streaming — yields reasoning trace steps
    as they are produced by each node.
    """
    graph = build_graph()

    initial_state: ShipmentState = {
        "raw_input": query,
        "world_event": world_event,
        "parsed_constraints": None,
        "resolved_hubs": None,
        "risk_scenario": None,
        "route_candidates": None,
        "pricing_data": None,
        "weather_data": None,
        "congestion_data": None,
        "sustainability_data": None,
        "scored_routes": None,
        "recommendation": None,
        "alternatives": None,
        "reasoning_summary": None,
        "trade_off_analysis": None,
        "reasoning_trace": [],
        "error": None
    }

    prev_trace_len = 0

    async for event in graph.astream(initial_state, stream_mode="values"):
        current_trace = event.get("reasoning_trace", [])
        # Yield only new reasoning steps
        if len(current_trace) > prev_trace_len:
            for step in current_trace[prev_trace_len:]:
                yield {"type": "reasoning_step", "data": step}
            prev_trace_len = len(current_trace)

    # Yield final result
    yield {
        "type": "final_result",
        "data": {
            "recommendation": event.get("recommendation"),
            "alternatives": event.get("alternatives", []),
            "reasoning_summary": event.get("reasoning_summary"),
            "trade_off_analysis": event.get("trade_off_analysis"),
            "parsed_constraints": event.get("parsed_constraints"),
            "reasoning_trace": event.get("reasoning_trace", []),
            "sustainability_data": event.get("sustainability_data", []),
            "risk_scenario": event.get("risk_scenario"),
            "error": event.get("error")
        }
    }
