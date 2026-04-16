"""
FastAPI API routes for the Shipment Orchestration Agent.
Includes sync endpoint, SSE streaming endpoint, health check, and presets.
"""

import json
import asyncio
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException, File, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import os
import base64
from openai import AsyncOpenAI

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
                "query": "Ship 120 cartons of textiles (0.5x0.4x0.4 meters each) and 5 pallets of parts (1.2x1x1 meters each) from Dubai to Rotterdam under $4000",
                "tags": ["sea", "air", "multimodal"]
            },
            {
                "label": "Shanghai → Los Angeles (Express)",
                "query": "Urgent shipment from Shanghai to Los Angeles: 50 crates of electronics (0.8x0.6x0.6 meters each), need it in 3 days, budget up to $8000",
                "tags": ["air", "express"]
            },
            {
                "label": "Mumbai → London (Economical)",
                "query": "Ship 1000kg of textiles from Mumbai to London, cheapest option, can wait up to 20 days",
                "tags": ["sea", "budget"]
            },
            {
                "label": "Singapore → Hamburg (Reliable)",
                "query": "Ship 20 large pallets of heavy machinery (1x1x1.5 meters each) from Singapore to Hamburg, reliable delivery within 10 days, budget $5000",
                "tags": ["reliability", "multimodal"]
            },
            {
                "label": "Hong Kong → New York (Fast)",
                "query": "Rush delivery: 10 containers of medical supplies (0.4x0.4x0.4 meters each) from Hong Kong to New York in 2 days, cost is not a concern",
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
        result = await run_agent(
            request.query, 
            world_event=request.world_event.value, 
            chat_history=request.chat_history,
            parsed_constraints=request.parsed_constraints
        )

        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])

        return {
            "success": True,
            "recommendation": result.get("recommendation"),
            "alternatives": result.get("alternatives", []),
            "reasoning_summary": result.get("reasoning_summary"),
            "trade_off_analysis": result.get("trade_off_analysis"),
            "parsed_constraints": result.get("parsed_constraints"),
            "cargo_profile": result.get("cargo_profile"),
            "spatial_yield": result.get("spatial_yield"),
            "customs_compliance": result.get("customs_compliance"),
            "smart_contract": result.get("smart_contract"),
            "reasoning_trace": result.get("reasoning_trace", []),
            "sustainability_data": result.get("sustainability_data", []),
            "risk_scenario": result.get("risk_scenario"),
            "negotiation_log": result.get("negotiation_log")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent pipeline error: {str(e)}")


# ── SSE Streaming Endpoint ──────────────────────────────────────────────────

async def _event_generator(query: str, world_event: str = "normal", chat_history=None, parsed_constraints=None) -> AsyncGenerator[str, None]:
    """Generate SSE events from the agent pipeline."""
    try:
        async for event in run_agent_streaming(
            query, 
            world_event=world_event, 
            chat_history=chat_history,
            parsed_constraints=parsed_constraints
        ):
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
        _event_generator(
            request.query, 
            world_event=request.world_event.value, 
            chat_history=request.chat_history,
            parsed_constraints=request.parsed_constraints
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

# ── Voice & Vision Ingestion ────────────────────────────────────────────────

@router.post("/vision/parse")
async def vision_parse(file: UploadFile = File(...)):
    """Parse a shipping document image and extract details."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=400, detail="OpenAI API key not configured")
        
    client = AsyncOpenAI(api_key=api_key)
    
    content = await file.read()
    base64_image = base64.b64encode(content).decode('utf-8')
    mime_type = file.content_type
    
    prompt = "You are a logistics expert. Extract the following details from this shipping document: origin, destination, weight in kg, dimensions if any, and type of goods. Format your response into a single concise natural language sentence like: 'Ship 500kg of electronics from Dubai to Rotterdam.' Do not output anything else."
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=300
        )
        query_text = response.choices[0].message.content.strip()
        return {"success": True, "query": query_text}
    except Exception as e:
        error_msg = str(e)
        if "insufficient_quota" in error_msg:
            raise HTTPException(status_code=429, detail="OpenAI API Quota Exceeded. Vision API unavailable.")
        raise HTTPException(status_code=500, detail=f"Vision API error: {error_msg}")


@router.post("/voice/transcribe")
async def voice_transcribe(file: UploadFile = File(...)):
    """Transcribe a voice memo into text."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=400, detail="OpenAI API key not configured")
        
    client = AsyncOpenAI(api_key=api_key)
    
    temp_file_path = f"temp_{file.filename}"
    try:
        content = await file.read()
        with open(temp_file_path, "wb") as f:
            f.write(content)
            
        with open(temp_file_path, "rb") as audio_file:
            transcript = await client.audio.translations.create(
                model="whisper-1", 
                file=audio_file
            )
        
        os.remove(temp_file_path)
        return {"success": True, "query": transcript.text}
    except Exception as e:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            
        error_msg = str(e)
        if "insufficient_quota" in error_msg:
            raise HTTPException(status_code=429, detail="OpenAI API Quota Exceeded. Voice transcribe unavailable.")
        raise HTTPException(status_code=500, detail=f"Voice API error: {error_msg}")

