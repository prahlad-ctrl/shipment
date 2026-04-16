"""
Shared state definition for the LangGraph agent orchestration.
This TypedDict defines the state that flows through all agent nodes.
"""

from typing import TypedDict, List, Optional, Dict, Any, Annotated
import operator


class ShipmentState(TypedDict):
    """
    The shared state that flows through the entire LangGraph agent pipeline.
    
    Each agent node reads from and writes to specific fields.
    The reasoning_trace field uses Annotated + operator.add so that
    each node can append trace entries without overwriting.
    """
    # Input
    raw_input: str
    
    # World event / risk scenario (normal, suez_canal_blocked, port_strike, atlantic_storm)
    world_event: Optional[str]
    
    # Conversational state
    chat_history: Optional[List[Dict[str, str]]]
    target_language: Optional[str]
    
    # Parser output
    parsed_constraints: Optional[Dict[str, Any]]
    
    # Cargo Analysis output
    cargo_profile: Optional[Dict[str, Any]]
    
    # Spatial Yield / Bin Packing output
    spatial_yield: Optional[Dict[str, Any]]
    
    # Customs Compliance output
    customs_compliance: Optional[Dict[str, Any]]
    
    # Hub Resolver output
    resolved_hubs: Optional[Dict[str, Any]]
    
    # Risk Scenario output
    risk_scenario: Optional[Dict[str, Any]]
    
    # Route Generator output  
    route_candidates: Optional[List[Dict[str, Any]]]
    
    # Enrichment outputs (from parallel agents)
    pricing_data: Optional[List[Dict[str, Any]]]
    weather_data: Optional[List[Dict[str, Any]]]
    congestion_data: Optional[List[Dict[str, Any]]]
    sustainability_data: Optional[List[Dict[str, Any]]]
    
    # Evaluator output
    scored_routes: Optional[List[Dict[str, Any]]]
    
    # Negotiation output
    negotiation_log: Optional[List[Dict[str, str]]]
    
    # Decision output
    recommendation: Optional[Dict[str, Any]]
    alternatives: Optional[List[Dict[str, Any]]]
    reasoning_summary: Optional[str]
    trade_off_analysis: Optional[str]
    
    # Generated code output
    smart_contract: Optional[Dict[str, Any]]
    
    # Accumulated reasoning trace (append-only via operator.add)
    reasoning_trace: Annotated[List[Dict[str, Any]], operator.add]
    
    # Error tracking
    error: Optional[str]
