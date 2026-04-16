"""
FastAPI application entry point for the Shipment Orchestration Agent.
"""

import os
import sys
import io
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

# Fix Windows console encoding for unicode
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

load_dotenv()

from api.routes import router
from api.auth import router as auth_router
from agent.graph import get_llm


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    print("\n" + "=" * 60)
    print("[STARTUP] Shipment Orchestration Agent")
    print("=" * 60)

    # Initialize LLM connection
    llm = get_llm()
    if llm:
        print("[OK] LLM connection established")
    else:
        print("[WARN] No LLM available -- running in algorithmic mode")
        print("       Set GOOGLE_API_KEY or start Ollama for AI-powered reasoning")

    print("=" * 60 + "\n")

    yield

    # Shutdown
    print("\n[SHUTDOWN] Shipment Orchestration Agent\n")


app = FastAPI(
    title="Shipment Orchestration Agent",
    description=(
        "AI-powered multi-agent system for optimal shipment route selection. "
        "Evaluates air, sea, and road options based on cost, SLA, weather, "
        "and port congestion to recommend the best shipping strategy."
    ),
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(router)
app.include_router(auth_router)


# Root endpoint
@app.get("/")
async def root():
    return {
        "service": "Shipment Orchestration Agent",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host=host, port=port, reload=True)
