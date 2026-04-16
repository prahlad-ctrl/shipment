"""
Pydantic models for API request/response schemas and internal data structures.
All agent nodes communicate through these strongly-typed models.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


# ── Enums ────────────────────────────────────────────────────────────────────

class TransportMode(str, Enum):
    AIR = "air"
    SEA = "sea"
    ROAD = "road"
    MULTIMODAL = "multimodal"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    SEVERE = "severe"


class CongestionLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class Priority(str, Enum):
    COST = "cost"
    SPEED = "speed"
    BALANCED = "balanced"
    RELIABILITY = "reliability"


# ── Request Models ───────────────────────────────────────────────────────────

class WorldEvent(str, Enum):
    NORMAL = "normal"
    SUEZ_CANAL_BLOCKED = "suez_canal_blocked"
    PORT_STRIKE = "port_strike"
    ATLANTIC_STORM = "atlantic_storm"


class ShipmentRequest(BaseModel):
    """Incoming shipment planning request."""
    query: str = Field(..., description="Natural language shipment request", min_length=5)
    world_event: WorldEvent = Field(default=WorldEvent.NORMAL, description="Active world event for risk simulation")


# ── Parsed Constraints ───────────────────────────────────────────────────────

class ParsedConstraints(BaseModel):
    """Structured constraints extracted from natural language input."""
    origin: str = Field(..., description="Origin city/port")
    destination: str = Field(..., description="Destination city/port")
    weight_kg: float = Field(..., description="Shipment weight in kilograms", gt=0)
    deadline_days: Optional[int] = Field(None, description="Maximum delivery time in days")
    budget_usd: Optional[float] = Field(None, description="Maximum budget in USD")
    priority: Priority = Field(default=Priority.BALANCED, description="Optimization priority")
    cargo_type: Optional[str] = Field(None, description="Type of cargo (general, perishable, hazardous, fragile)")
    special_requirements: Optional[List[str]] = Field(default_factory=list, description="Any special requirements")


# ── Route Models ─────────────────────────────────────────────────────────────

class RouteLeg(BaseModel):
    """A single leg of a multi-leg route."""
    from_location: str = Field(..., description="Departure location")
    to_location: str = Field(..., description="Arrival location")
    mode: TransportMode = Field(..., description="Transport mode for this leg")
    carrier: Optional[str] = Field(None, description="Suggested carrier")
    distance_km: float = Field(..., description="Distance in kilometers")
    duration_hours: float = Field(..., description="Estimated duration in hours")


class RouteCandidate(BaseModel):
    """A candidate route with its legs."""
    id: str = Field(..., description="Unique route identifier")
    name: str = Field(..., description="Human-readable route name")
    mode: TransportMode = Field(..., description="Primary transport mode")
    legs: List[RouteLeg] = Field(..., description="Ordered list of route legs")
    total_distance_km: float = Field(..., description="Total route distance")
    estimated_days: float = Field(..., description="Estimated transit days")
    waypoints: Optional[List[List[float]]] = Field(default=None, description="Map waypoints [[lat, lng], ...]")


# ── Cost Models ──────────────────────────────────────────────────────────────

class CostBreakdown(BaseModel):
    """Itemized cost breakdown for a route."""
    carrier_name: str = Field(..., description="Carrier name")
    freight: float = Field(..., description="Base freight cost")
    fuel_surcharge: float = Field(..., description="Fuel surcharge")
    customs_and_docs: float = Field(..., description="Customs and documentation fees")
    insurance: float = Field(..., description="Cargo insurance")
    handling: float = Field(..., description="Handling fees")
    total: float = Field(..., description="Total cost")
    currency: str = Field(default="USD")


class RoutePricing(BaseModel):
    """Pricing data for a route."""
    route_id: str
    cost_breakdown: CostBreakdown
    within_budget: Optional[bool] = None
    budget_delta: Optional[float] = None  # positive = under budget, negative = over


# ── Weather Models ───────────────────────────────────────────────────────────

class WeatherCondition(BaseModel):
    """Weather condition at a location."""
    location: str
    zone: str
    risk_level: RiskLevel
    risk_score: float
    conditions: str
    estimated_delay_hours: float
    wind_speed_knots: float
    wave_height_m: float


class RouteWeather(BaseModel):
    """Weather assessment for a route."""
    route_id: str
    overall_risk_level: RiskLevel
    overall_risk_score: float
    total_delay_hours: float
    worst_conditions: List[str]
    location_breakdown: List[WeatherCondition]


# ── Congestion Models ────────────────────────────────────────────────────────

class PortCongestion(BaseModel):
    """Congestion data for a port."""
    port_name: str
    congestion_level: CongestionLevel
    congestion_score: float
    queue_time_hours: float
    berth_availability_pct: float
    estimated_delay_hours: float
    vessels_in_queue: int
    advisory: str


class RouteCongestion(BaseModel):
    """Congestion data for a route's ports."""
    route_id: str
    overall_congestion: CongestionLevel
    overall_score: float
    total_delay_hours: float
    bottleneck_port: Optional[str]
    port_breakdown: List[PortCongestion]


# ── Scored Route ─────────────────────────────────────────────────────────────

class ScoredRoute(BaseModel):
    """A fully evaluated and scored route."""
    route: RouteCandidate
    pricing: RoutePricing
    weather: RouteWeather
    congestion: RouteCongestion
    overall_score: float = Field(..., description="Composite score (0-100)")
    cost_score: float = Field(..., description="Cost efficiency score (0-100)")
    time_score: float = Field(..., description="Time performance score (0-100)")
    risk_score: float = Field(..., description="Risk assessment score (0-100, higher=safer)")
    reliability_score: float = Field(..., description="Overall reliability score (0-100)")
    pros: List[str] = Field(default_factory=list)
    cons: List[str] = Field(default_factory=list)
    is_recommended: bool = Field(default=False)


# ── Reasoning ────────────────────────────────────────────────────────────────

class ReasoningStep(BaseModel):
    """A single step in the agent's reasoning trace."""
    agent: str = Field(..., description="Agent name that produced this step")
    step: str = Field(..., description="Step description")
    detail: str = Field(..., description="Detailed reasoning or data")
    icon: Optional[str] = Field(None, description="Emoji icon for UI display")
    data: Optional[Dict[str, Any]] = Field(None, description="Structured data for this step")


# ── Final Response ───────────────────────────────────────────────────────────

class ShipmentPlan(BaseModel):
    """The complete shipment plan response."""
    success: bool = True
    recommendation: ScoredRoute = Field(..., description="The recommended route")
    alternatives: List[ScoredRoute] = Field(default_factory=list, description="Alternative routes")
    reasoning_summary: str = Field(..., description="Human-readable summary of the decision")
    trade_off_analysis: str = Field(..., description="Cost vs speed vs risk analysis")
    reasoning_trace: List[ReasoningStep] = Field(default_factory=list, description="Full agent reasoning trace")
    parsed_constraints: ParsedConstraints = Field(..., description="Parsed input constraints")


class ErrorResponse(BaseModel):
    """Error response."""
    success: bool = False
    error: str
    detail: Optional[str] = None
