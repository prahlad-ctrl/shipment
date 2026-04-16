"""
FastAPI API routes for the Shipment Orchestration Agent.
Includes sync endpoint, SSE streaming endpoint, health check, and presets.
"""

import json
import asyncio
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from api.schemas import ShipmentRequest, ErrorResponse
from agent.graph import run_agent, run_agent_streaming

router = APIRouter(prefix="/api", tags=["shipment"])


# ── Health Check ─────────────────────────────────────────────────────────────

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "shipment-orchestration-agent"}


# ── Preset Examples ──────────────────────────────────────────────────────────

@router.get("/routes/presets")
async def get_presets():
    """Return example shipment queries for the UI."""
    return {
        "presets": [
            {
                "label": "Dubai → Rotterdam (Budget)",
                "query": "Ship 500kg from Dubai to Rotterdam within 5 days under $4000",
                "tags": ["sea", "air", "multimodal"]
            },
            {
                "label": "Shanghai → Los Angeles (Express)",
                "query": "Urgent shipment of 200kg from Shanghai to Los Angeles, need it in 3 days, budget up to $8000",
                "tags": ["air", "express"]
            },
            {
                "label": "Mumbai → London (Economical)",
                "query": "Ship 1000kg of textiles from Mumbai to London, cheapest option, can wait up to 20 days",
                "tags": ["sea", "budget"]
            },
            {
                "label": "Singapore → Hamburg (Reliable)",
                "query": "Ship 750kg of electronics from Singapore to Hamburg, need reliable delivery within 10 days, budget $5000",
                "tags": ["reliability", "multimodal"]
            },
            {
                "label": "Hong Kong → New York (Fast)",
                "query": "Rush delivery: 300kg from Hong Kong to New York in 2 days, cost is not a concern",
                "tags": ["air", "express", "urgent"]
            }
        ]
    }


# ── World Event Options ──────────────────────────────────────────────────────

@router.get("/world-events")
async def get_world_events():
    """Return available world event scenarios for the UI."""
    return {
        "events": [
            {"id": "normal", "label": "Normal", "icon": "✅", "description": "No special global disruptions."},
            {"id": "suez_canal_blocked", "label": "Suez Canal Blocked", "icon": "🚢", "description": "Suez Canal is blocked, sea routes rerouted via Cape of Good Hope."},
            {"id": "port_strike", "label": "European Port Strike", "icon": "⚠️", "description": "Major European ports on strike, severe arrival delays."},
            {"id": "atlantic_storm", "label": "Atlantic Storm", "icon": "🌀", "description": "Severe Atlantic storms causing delays on trans-Atlantic routes."}
        ]
    }


# ── Synchronous Planning Endpoint ────────────────────────────────────────────

@router.post("/shipment/plan")
async def create_shipment_plan(request: ShipmentRequest):
    """
    Run the full agent pipeline and return the complete shipment plan.
    """
    try:
        result = await run_agent(request.query, world_event=request.world_event.value)

        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])

        return {
            "success": True,
            "recommendation": result.get("recommendation"),
            "alternatives": result.get("alternatives", []),
            "reasoning_summary": result.get("reasoning_summary"),
            "trade_off_analysis": result.get("trade_off_analysis"),
            "parsed_constraints": result.get("parsed_constraints"),
            "reasoning_trace": result.get("reasoning_trace", []),
            "sustainability_data": result.get("sustainability_data", []),
            "risk_scenario": result.get("risk_scenario")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent pipeline error: {str(e)}")


# ── SSE Streaming Endpoint ──────────────────────────────────────────────────

async def _event_generator(query: str, world_event: str = "normal") -> AsyncGenerator[str, None]:
    """Generate SSE events from the agent pipeline."""
    try:
        async for event in run_agent_streaming(query, world_event=world_event):
            data = json.dumps(event, default=str)
            yield f"data: {data}\n\n"

        # Signal completion
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
    except Exception as e:
        error_event = json.dumps({"type": "error", "data": {"message": str(e)}})
        yield f"data: {error_event}\n\n"


@router.post("/shipment/plan/stream")
async def stream_shipment_plan(request: ShipmentRequest):
    """
    Stream the agent's reasoning process via Server-Sent Events.
    Each step is streamed as it completes, giving real-time visibility
    into the agent's decision-making process.
    """
    return StreamingResponse(
        _event_generator(request.query, world_event=request.world_event.value),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
