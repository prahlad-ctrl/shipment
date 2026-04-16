# 🚢 ShipRoute AI — Intelligent Shipment Orchestration Agent

> AI-powered multi-agent system that finds the optimal shipping route across Air, Sea, Road, and Rail — factoring in cost, transit time, weather risk, port congestion, and carbon emissions in real-time.

---

## 📌 Problem Statement

Global supply chain logistics requires evaluating **dozens of variables** — transport modes, carrier pricing, weather disruptions, port congestion, geopolitical events — just to ship a single package. Logistics managers spend hours comparing options manually, often missing critical risk factors that lead to delayed deliveries and budget overruns.

**There is no single tool** that combines intelligent route generation, real-time risk assessment, cost optimization, and sustainability tracking into one decision engine.

---

## 💡 Solution

**ShipRoute AI** is a **multi-agent AI orchestration platform** that automates the entire shipment planning lifecycle:

1. **Multi-Modal Input (Text, Voice, Vision)** — Input parameters via natural language, speak into the mic, or upload a photo of a shipping manifest for automatic AI extraction.
2. **AI-Powered Parsing & Fallback Engine** — Extracts origin, destination, weight, dimensions, and budget using LLM. A robust regex fallback engine ensures **zero-downtime** even if the AI hits rate limits.
3. **Multi-Modal Route Generation** — Dynamically generates route candidates across **Air, Sea, Road, and Rail** with real geographic feasibility checks (OSRM land-connectivity verification).
4. **Parallel Risk Enrichment** — Simultaneously evaluates pricing, weather, port congestion, and carbon sustainability for each route.
5. **Intelligent Scoring & Recommendation** — Scores all routes on a weighted composite scale and recommends the optimal choice.
6. **Interactive World Map & Animated Tracker** — Renders routes on a real-world interactive map with an animated timeline scrubber to simulate transport phases geographically.
7. **3D Volumetric Cargo Engine** — Leverages WebGL/Three.js to visualize precise box/pallet dimensions packed inside a standard TEU container.
8. **Automated AI Negotiation** — A dedicated LangGraph Broker Agent negotiates spot discounts dynamically with the chosen carrier.
9. **Blockchain Smart Contract Escrow** — Simulates a Web3 Escrow sequence confirming payment lock, decentralized tracking handoffs, and final cryptographic release on delivery.
10. **World Event Simulation** — Simulate disruptions like Suez Canal blockage, port strikes, or Atlantic storms to see how routes dynamically adapt.

---

## 🛠️ Tech Stack

### Backend
| Technology | Purpose |
|---|---|
| **Python 3.11+** | Core backend language |
| **FastAPI** | High-performance async REST API framework |
| **LangGraph** | Multi-agent orchestration graph (directed acyclic pipeline) |
| **LangChain** | LLM abstraction layer for prompt engineering |
| **OpenAI GPT-4o-mini** | Primary LLM for natural language parsing & reasoning |
| **Google Gemini** | Secondary LLM fallback |
| **Ollama** | Local LLM fallback (offline mode) |
| **Pydantic** | Request/response schema validation |
| **OSRM API** | Road connectivity verification (land-bridge detection) |
| **Nominatim API** | Geocoding for arbitrary global locations |
| **Uvicorn** | ASGI server with hot-reload |

### Frontend
| Technology | Purpose |
|---|---|
| **React 19** | Component-based UI framework |
| **Vite 8** | Lightning-fast dev server & bundler |
| **Three.js & React Three Fiber** | WebGL canvas for 3D container visualization |
| **Leaflet + React-Leaflet** | Interactive world map with animated route tracking |
| **Framer Motion** | Smooth micro-animations & transitions |
| **Lucide React** | Premium icon library |
| **Vanilla CSS** | Custom glassmorphic light-mode premium design system |

### Data & APIs
| Source | Purpose |
|---|---|
| `ports.json` | Pre-indexed coordinates for 15+ major logistics hubs |
| `carriers.json` | Carrier database (Air, Sea, Road, Rail) with base rates |
| `routes_db.json` | Pre-defined shipping corridors with leg-level details |
| **OpenStreetMap/CARTO** | Map tile layer for interactive visualization |

---

## 🏗️ Architecture — Model View Controller (MVC)

```
┌─────────────────────────────────────────────────────┐
│                   FRONTEND (View)                   │
│                  React + Vite + CSS                 │
├─────────────────────────────────────────────────────┤
│  Login.jsx          │  Auth gate (Sign In / Sign Up)│
│  ShipmentInput.jsx  │  Query input + world events   │
│  AgentReasoning.jsx │  Live reasoning stream        │
│  DecisionSummary.jsx│  Recommended route + metrics  │
│  RouteMap.jsx         │  Interactive Leaflet map       │
│  TimelineScrubber.jsx │  Animation control for map     │
│  RouteComparison.jsx  │  Side-by-side route cards      │
│  CostBreakdown.jsx    │  Itemized pricing table        │
│  Container3D.jsx      │  WebGL 3D Cargo Load visualization│
│  SmartContractEscrow.jsx│  Web3 transaction UI           │
│  RouteCard.jsx        │  Individual route score card   │
└────────────────┬────────────────────────────────────┘
                 │ HTTP / SSE (Server-Sent Events)
                 ▼
┌─────────────────────────────────────────────────────┐
│                BACKEND (Controller)                 │
│              FastAPI + LangGraph Engine             │
├─────────────────────────────────────────────────────┤
│  api/routes.py      │  REST endpoints & SSE stream  │
│  api/schemas.py     │  Pydantic request/response    │
│  agent/graph.py     │  LangGraph pipeline builder   │
│  agent/state.py     │  Shared TypedDict state       │
└────────────────┬────────────────────────────────────┘
                 │ Internal Pipeline (LangGraph DAG)
                 ▼
┌─────────────────────────────────────────────────────┐
│              AGENT NODES (Model / Logic)            │
│          Multi-Agent AI Processing Pipeline         │
├─────────────────────────────────────────────────────┤
│  parser.py          │  NLP → structured constraints │
│  hub_resolver.py    │  Location → logistics hub     │
│  route_generator.py │  Generate multi-modal routes  │
│  risk_scenario.py   │  World event impact analysis  │
│  pricing.py         │  Cost estimation per route    │
│  weather.py         │  Weather risk assessment      │
│  port_congestion.py │  Port delay forecasting       │
│  sustainability.py  │  Carbon emission calculation  │
│  evaluator.py       │  Composite scoring engine     │
│  negotiation.py     │  AI broker rate negotiations  │
│  decision.py        │  Final recommendation logic   │
├─────────────────────────────────────────────────────┤
│              TOOLS (Model / Data Layer)             │
├─────────────────────────────────────────────────────┤
│  geo_utils.py       │  Geocoding, distance, OSRM    │
│  pricing_simulator  │  Carrier rate calculations    │
│  weather_simulator  │  Weather condition generation │
│  port_simulator     │  Congestion level simulation  │
└─────────────────────────────────────────────────────┘
```

### Proper Agentic Workflow (LangGraph Engine)

The backend is driven by a decentralized, multi-agent AI system built using LangGraph. The pipeline is designed around 10 distinct AI agents, operating in a mix of sequential dependencies and parallel enrichment paths.

1. **Parser Node (`parser.py`)**: Consumes raw natural language. Uses an LLM to accurately structure variables: `{origin, destination, budget, deadline, constraints}`. If API quotas exhaust, it triggers an airtight deterministic Regex extraction.
2. **Hub Resolver Node (`hub_resolver.py`)**: Normalizes vague locations like "Middle East" to exact ports (e.g., *Jebel Ali (AEJEA)*), querying geolocation constraints via OSRM spatial validation.
3. **Route Generator Node (`route_generator.py`)**: Generates realistic combinatorial multimodal route candidates (Air, Sea, Road, Multimodal) leveraging the `routes_db.json` matrix and active landbridge connectivity algorithms.
4. **Risk Scenario Node (`risk_scenario.py`)**: Cross-references global configurations (e.g., "Suez Canal blocked"). Reroutes affected sea shipments around the Horn of Africa, instantly recalculating the Haversine distances.
5. **Parallel Enrichment Nodes** (Executing concurrently to bypass high Latency):
   - **Pricing Agent (`pricing.py`)**: Extracts raw carrier logs and aggregates Fuel, Freight, and Insurance surcharges dynamically.
   - **Weather Agent (`weather.py`)**: Assesses cyclone, hurricane, and blizzard anomalies along the specific spatial corridor.
   - **Port Congestion Agent (`port_congestion.py`)**: Fakes real-time transit queue logic across global seaports.
   - **Sustainability Agent (`sustainability.py`)**: Tallies the total footprint (Tons CO₂) based on multimodal transport standards and payload weight.
6. **Evaluator Node (`evaluator.py`)**: Evaluates every route utilizing the parallelly enriched data. Formulates a weighted "Composite Score" (Time, Risk, Budget, and Eco footprint).
7. **Negotiation Node (`negotiation.py`)**: The AI broker agent. Dynamically drafts and counter-offers proposals to simulated carrier APIs, fetching hidden transit discounts.
8. **Decision Node (`decision.py`)**: Filters down to the absolute optimal path, caches alternates, and drafts the overarching human-readable summary.

```
User Query
    │
    ▼
┌─────────┐    ┌──────────────┐    ┌─────────────────┐    ┌────────────────┐
│ Parser  │───▶│ Hub Resolver │───▶│ Route Generator │───▶│ Risk Scenario  │
└─────────┘    └──────────────┘    └─────────────────┘    └───────┬────────┘
                                                                  │
                           ┌───────────────────────────┬──────────┴───────────────┬───────────────────────────┐
                           ▼                           ▼                          ▼                           ▼
                   ┌──────────────┐             ┌────────────┐             ┌─────────────┐             ┌──────────────┐
                   │ Pricing Node │             │ Weather AI │             │ Port Traffic│             │ Eco-Tracking │
                   └──────┬───────┘             └──────┬─────┘             └──────┬──────┘             └──────┬───────┘
                          │                            │                          │                           │
                          └────────────────────────────┼──────────────────────────┼───────────────────────────┘
                                                       ▼
                                               ┌──────────────┐
                                               │  Evaluator   │
                                               └──────┬───────┘
                                                      ▼
                                               ┌──────────────┐
                                               │  Negotiation │
                                               └──────┬───────┘
                                                      ▼
                                               ┌──────────────┐
                                               │   Decision   │───▶ Result
                                               └──────────────┘
```

---

## 🚀 How to Run

### Prerequisites
- **Python 3.11+**
- **Node.js 18+**
- An **OpenAI API key** (or Google Gemini key, or local Ollama instance)

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/shipment.git
cd shipment
```

## 🔑 Environment Variables & API Keys

The application utilizes a cascading LLM fallback engine designed for zero downtime (`Gemini 1.5 Flash` → `GPT-4o-Mini` → `Local Ollama`). To fully leverage AI reasoning, clone the `.env.example` inside `backend/` to `.env` and fill out your keys:

```dotenv
# 1. Primary Cloud LLM (Highly Recommended)
GOOGLE_API_KEY=your_gemini_api_key_here    # Primary: Faster and handles long contexts
OPENAI_API_KEY=your_openai_api_key_here    # Secondary: Fallback

# 2. Local/Offline LLM Fallback (Zero Setup Offline Ops)
OLLAMA_BASE_URL=http://localhost:11434     # Requires Ollama running locally
OLLAMA_MODEL=llama3:8b                     

# 3. Microservice / DB Configs
JWT_SECRET=shiproute-ai-change-this-to-a-random-secret  # Auth
SMTP_HOST=smtp.gmail.com                   # Optional MFA OTP
SMTP_PORT=587
```

### 2. Backend Setup
```bash
cd backend

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Start the backend server
python main.py
```
The backend will start at **http://localhost:8000**. API docs available at **/docs**.

### 3. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```
The frontend will start at **http://localhost:5173**.

### 4. Use the Application
1. Open **http://localhost:5173** in your browser
2. **Sign Up / Sign In** on the login page
3. Enter a shipment query or click a preset (e.g., *"Dubai → Rotterdam"*)
4. Select world conditions (Normal, Suez Canal Blocked, Port Strike, etc.)
5. Click **Plan Route** and watch the AI agents reason in real-time
6. View the recommended route on the interactive map with full cost breakdown

---

## 📁 Project Structure

```
idek-just-anything-/
├── backend/
│   ├── main.py                 # FastAPI app entry point
│   ├── requirements.txt        # Python dependencies
│   ├── .env.example            # Environment variables template
│   ├── api/
│   │   ├── routes.py           # REST API endpoints
│   │   └── schemas.py          # Pydantic data models
│   ├── agent/
│   │   ├── graph.py            # LangGraph pipeline orchestration
│   │   ├── state.py            # Shared pipeline state definition
│   │   └── nodes/
│   │       ├── parser.py       # Natural language → constraints
│   │       ├── hub_resolver.py # Location → logistics hub
│   │       ├── route_generator.py  # Multi-modal route creation
│   │       ├── risk_scenario.py    # World event impact analysis
│   │       ├── pricing.py      # Cost estimation
│   │       ├── weather.py      # Weather risk assessment
│   │       ├── port_congestion.py  # Port delay forecasting
│   │       ├── sustainability.py   # Carbon emission tracking
│   │       ├── evaluator.py    # Composite scoring engine
│   │       └── decision.py     # Final recommendation
│   ├── tools/
│   │   ├── geo_utils.py        # Geocoding, OSRM, Haversine
│   │   ├── pricing_simulator.py
│   │   ├── weather_simulator.py
│   │   └── port_simulator.py
│   └── data/
│       ├── ports.json          # Global logistics hub coordinates
│       ├── carriers.json       # Carrier database (air/sea/road/rail)
│       └── routes_db.json      # Pre-defined shipping corridors
│
├── frontend/
│   ├── index.html              # HTML entry point
│   ├── package.json            # Node.js dependencies
│   ├── vite.config.js          # Vite + React plugin config
│   └── src/
│       ├── main.jsx            # React entry point
│       ├── App.jsx             # Root component with auth gate
│       ├── index.css           # Glassmorphic design system
│       ├── components/
│       │   ├── Login.jsx       # Sign In / Sign Up page
│       │   ├── Header.jsx      # App header with branding
│       │   ├── ShipmentInput.jsx   # Query input + presets
│       │   ├── AgentReasoningStream.jsx  # Live reasoning timeline
│       │   ├── DecisionSummary.jsx # Recommendation dashboard
│       │   ├── RouteMap.jsx    # Interactive Leaflet map
│       │   ├── RouteComparison.jsx # Route cards grid
│       │   ├── RouteCard.jsx   # Individual route card
│       │   ├── CostBreakdown.jsx   # Pricing table
│       │   ├── WeatherBadge.jsx    # Weather risk indicator
│       │   └── CongestionMeter.jsx # Port congestion gauge
│       └── utils/
│           ├── api.js          # Backend API client (fetch + SSE)
│           └── formatters.js   # Currency, date, mode formatters
│
└── README.md
```

---

## 🌍 Key Features

- **🤖 Multi-Agent AI Pipeline** — 10 specialized agents working in concert via LangGraph
- **✈️🚢🚛🚂 4 Transport Modes** — Air, Sea, Road, Rail with feasibility checks
- **🗺️ Interactive Map** — Real-world route visualization on OpenStreetMap
- **⚡ Real-Time Streaming** — Watch AI agents reason step-by-step via SSE
- **🌪️ World Event Simulation** — Test routes against Suez blockage, port strikes, storms
- **📊 Composite Scoring** — Cost, time, risk, reliability weighted scoring
- **🌱 Sustainability Tracking** — CO₂ emissions per route with eco-labels
- **🔒 Authentication** — Sign In / Sign Up with session management
- **🎨 Premium UI** — Glassmorphic dark-mode design with micro-animations

---

## 📜 License

MIT License — Built for HackStrom 2026
