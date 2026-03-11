<div align="center">

# CampaignX

### Autonomous Multi-Agent Email Campaign Optimizer for BFSI

**FrostHack XPECTO 2026 @ IIT Mandi — Team Four Musketeers**

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-1C3C3C?logo=langchain&logoColor=white)](https://langchain-ai.github.io/langgraph/)
[![Groq](https://img.shields.io/badge/Groq-Llama_3.3_70B-F55036)](https://groq.com)
[![React](https://img.shields.io/badge/React-TypeScript-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)

</div>

---

CampaignX is an end-to-end agentic system that autonomously runs email marketing campaigns for the banking & financial services sector. It parses a natural-language brief, segments 1,000 real customers into micro-audiences, generates A/B-tested email variants with per-segment personalization, executes campaigns via a live API, and iteratively optimizes based on real open/click metrics — all orchestrated by a LangGraph multi-agent pipeline with human-in-the-loop approval.

---

## Table of Contents

- [System Architecture](#system-architecture)
- [Agent Pipeline](#agent-pipeline)
- [Key Features](#key-features)
- [Live Results](#live-results)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [How It Works](#how-it-works)
- [Team](#team)

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                        LangGraph Orchestrator                        │
│                                                                      │
│  ┌──────────┐   ┌───────────┐   ┌───────────┐   ┌──────────────┐   │
│  │   Tool    │──▶│   Brief   │──▶│ Customer  │──▶│   Strategy   │   │
│  │ Discovery │   │  Parser   │   │ Profiler  │   │   Planner    │   │
│  └──────────┘   └───────────┘   └───────────┘   └──────┬───────┘   │
│                                                         │           │
│  ┌──────────────────────────────────────────────────────┘           │
│  │                                                                  │
│  ▼                                                                  │
│  ┌───────────┐   ┌───────────┐   ┌───────────┐   ┌──────────────┐  │
│  │ Creative  │──▶│   HITL    │──▶│ Executor  │──▶│   Metrics    │  │
│  │ Generator │   │ Approval  │   │ (A/B Send)│   │   Fetcher    │  │
│  └───────────┘   └───────────┘   └───────────┘   └──────┬───────┘  │
│                       ▲                                  │          │
│                       │         ┌──────────────┐         │          │
│                       │         │  Analytics & │◀────────┘          │
│                       │         │  Optimizer   │                    │
│                       │         └──────┬───────┘                    │
│                       │                │                            │
│                       │     ┌──────────┴──────────┐                 │
│                       │     ▼                     ▼                 │
│                       │  [Improve?]          [Done ✓]               │
│                       │     │                     │                 │
│                       │     ▼                     ▼                 │
│                       └── Loop ──           ┌──────────┐           │
│                                             │  Final   │           │
│                                             │  Send    │──▶ END    │
│                                             └──────────┘           │
│                                                                     │
│  ┌──────────────┐   ┌──────────────┐                               │
│  │ Error Handler│   │ MemorySaver  │  (checkpointing & recovery)   │
│  └──────────────┘   └──────────────┘                               │
└──────────────────────────────────────────────────────────────────────┘
         │                                          │
         ▼                                          ▼
┌─────────────────┐                      ┌─────────────────────┐
│  CampaignX API  │                      │  React Dashboard    │
│  (Live / Prism) │                      │  (Vite + Tailwind)  │
└─────────────────┘                      └─────────────────────┘
```

---

## Agent Pipeline

| # | Agent | Role | Key Logic |
|---|-------|------|-----------|
| 1 | **Tool Discovery** | Parses `campaignx_api.json` (OpenAPI 3.1) at runtime into executable `StructuredTool` instances | Dynamic endpoint registration — no hardcoded API calls |
| 2 | **Brief Parser** | Converts natural-language marketing brief → structured `ParsedBrief` | Pydantic structured output via Groq |
| 3 | **Customer Profiler** | Fetches 1,000 customers, segments into 5 micro-segments by age/gender/income | Income threshold: ₹3.5L/month for high-income |
| 4 | **Strategy Planner** | Creates 2 A/B variants per segment with distinct tones | Programmatic retry if LLM generates same tone for both |
| 5 | **Creative Generator** | Writes compliant email HTML per variant with segment-specific offers | Banned-word detection, HTML dedup, offer filtering |
| 6 | **HITL Approval** | Pauses graph; human reviews variants before any API call | Approve / Reject+Feedback loop |
| 7 | **Executor** | 50/50 A/B customer split per segment → `send_campaign` API | Real-time scheduling with future timestamps |
| 8 | **Metrics Fetcher** | Fetches per-customer EO/EC rows → computes open/click rates | Raw count aggregation from report API |
| 9 | **Analytics & Optimizer** | Per-segment winner selection, programmatic termination | Stops at <5% improvement or composite ≥ 0.85 |
| 10 | **Final Send** | Winner-take-all: sends best variant to ALL customers per segment | Maximizes total EO=Y + EC=Y count |

---

## Key Features

| Feature | Description |
|---------|-------------|
| **5 Micro-Segments** | Data-driven segmentation: Female/Male Seniors 60+, High-Income Working, Working Age 25-59, Young Adults 18-24 |
| **True A/B Testing** | 50/50 customer split per segment — not random, not global |
| **Winner-Take-All Final Send** | After optimization, the winning variant is sent to ALL customers in the segment |
| **Programmatic Termination** | No LLM decides when to stop — hard metrics thresholds prevent infinite loops |
| **Tone Enforcement** | Retry mechanism ensures A/B variants have distinct tones |
| **Segment-Specific Offers** | Senior offers never leak into youth emails, and vice versa |
| **Cross-Segment Tone Tracking** | A tone winning for seniors isn't banned globally if it loses for youth |
| **Compliance Engine** | Banned word detection + automatic regeneration for BFSI regulatory safety |
| **Self-Healing Errors** | API failures trigger error correction with retry caps (max 3) |
| **Full Observability** | Every LLM call, agent decision, and state transition traced via Langfuse |
| **Human-in-the-Loop** | Human approval required before every campaign execution |
| **Variant ID Normalization** | Handles LLM short-form IDs (`"v2"` → `"seg_young_adults_v2"`) gracefully |

---

## Live Results

Real API run on 1,000 customers (March 12, 2026):

### Iteration 1 — A/B Test Performance

| Segment | Customers | V1 Open | V1 Click | V2 Open | V2 Click | Winner |
|---------|-----------|---------|----------|---------|----------|--------|
| Female Senior 60+ | 204 | 0.0% | 0.0% | 0.0% | 0.0% | v1 (respectful) |
| Male Senior 60+ | 61 | 0.0% | 0.0% | 0.0% | 0.0% | v1 (authoritative) |
| High Income Working | 113 | 21.4% | 5.4% | 1.8% | 0.0% | **v1 (sophisticated)** |
| Working Age 25-59 | 304 | 47.4% | 19.1% | 46.1% | 23.0% | **v2 (modern, concise)** |
| Young Adults 18-24 | 318 | 26.4% | 0.0% | 26.4% | 0.0% | v1 (casual) |

### Final Send — Winner-Take-All

| Segment | Customers | Winning Tone | Projected EO | Projected EC |
|---------|-----------|-------------|--------------|-------------|
| Female Senior 60+ | 204 | Respectful | 0 | 0 |
| Male Senior 60+ | 61 | Authoritative | 0 | 0 |
| High Income Working | 113 | Sophisticated | ~24 | ~6 |
| Working Age 25-59 | 304 | Modern, concise | ~140 | ~70 |
| Young Adults 18-24 | 318 | Casual | ~84 | 0 |
| **Total** | **1,000** | | **~248** | **~76** |

> **Combined Score: ~324 (EO=Y + EC=Y)**

### Key Insight
> The working-age segment (304 customers) drives 65%+ of all engagement. Content tone matters less than segment-level engagement propensity — the system correctly identifies and doubles down on high-performing segments.

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Orchestration** | LangGraph + LangChain | Multi-agent graph with `MemorySaver` checkpointing |
| **LLM** | Groq — Llama 3.3 70B Versatile | High-speed inference, Pydantic structured output |
| **Backend** | FastAPI + Uvicorn | REST API with SQLite thread persistence |
| **Frontend** | React + TypeScript + Vite | Dark-themed FinTech dashboard |
| **Styling** | Tailwind CSS + shadcn/ui + Framer Motion | Component library with smooth animations |
| **Charts** | Recharts | Per-segment performance visualization |
| **Observability** | Langfuse | Full LLM tracing and cost tracking |
| **Mock Server** | Prism (Stoplight) | OpenAPI-based mock for offline testing |
| **API Spec** | OpenAPI 3.1 (`campaignx_api.json`) | Runtime tool discovery |

---

## Project Structure

```
CampaignX/
├── agents/                   # LangGraph agent nodes
│   ├── analytics.py          #   A/B analysis, winner selection, termination logic
│   ├── brief_parser.py       #   NL brief → ParsedBrief (Pydantic)
│   ├── creative.py           #   Email HTML generation with compliance checks
│   ├── error_handler.py      #   API error recovery with retry caps
│   ├── executor.py           #   A/B split execution + final winner-take-all send
│   ├── metrics.py            #   Report fetching, EO/EC rate computation
│   ├── profiler.py           #   Customer fetch/cache + 5-segment logic
│   └── strategy.py           #   A/B variant planning with tone enforcement
├── api/
│   └── main.py               # FastAPI backend (campaign CRUD, HITL endpoints)
├── tools/
│   └── discovery.py          # OpenAPI → StructuredTool runtime loader
├── frontend/                 # React + TypeScript dashboard
│   └── src/
│       ├── pages/
│       │   ├── Index.tsx      #   Campaign creation & HITL approval
│       │   └── Dashboard.tsx  #   Metrics visualization & variant cards
│       └── components/        #   shadcn/ui component library
├── tests/                    # Pytest test suite
├── graph.py                  # LangGraph state machine (nodes, edges, routing)
├── models.py                 # Pydantic models & CampaignState TypedDict
├── campaignx_api.json        # OpenAPI 3.1 spec for the CampaignX API
├── requirements.txt          # Python dependencies
├── .env.example              # Environment template with documentation
└── README.md
```

---

## Quick Start

### Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.11+ | [python.org](https://python.org) |
| Node.js | 18+ | [nodejs.org](https://nodejs.org) or `bun` |
| Groq API Key | — | [console.groq.com](https://console.groq.com) |

### 1. Clone & Configure

```bash
git clone https://github.com/Shrestha-Kumar/Frosthack.git
cd Frosthack
cp .env.example .env
# Edit .env and add your GROQ_API_KEY and CAMPAIGNX_API_KEY
```

### 2. Backend

```bash
# Install Python dependencies
pip install -r requirements.txt

# Start the API server
uvicorn api.main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
npm install    # or: bun install
npm run dev    # or: bun dev
```

Open **http://localhost:5173** — paste your marketing brief and go.

### 4. (Optional) Local Testing with Prism

To test without burning API quota:

```bash
# In a separate terminal
npx @stoplight/prism-cli mock campaignx_api.json

# Then in .env, set:
# CAMPAIGNX_API_BASE_URL=http://localhost:4010
# USE_CACHE=true
```

---

## Configuration

All configuration is via `.env` (see [.env.example](.env.example) for full documentation):

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GROQ_API_KEY` | Yes | — | Groq API key for Llama 3.3 70B |
| `CAMPAIGNX_API_BASE_URL` | Yes | — | Live API base URL |
| `CAMPAIGNX_API_KEY` | Yes | — | Team API key |
| `USE_CACHE` | No | `true` | Load customers from local cache (saves API calls) |
| `MOCK_MODE` | No | `false` | Use 50 dummy customers instead of real data |
| `LANGFUSE_PUBLIC_KEY` | No | — | Langfuse tracing (optional) |
| `LANGFUSE_SECRET_KEY` | No | — | Langfuse tracing (optional) |
| `LANGFUSE_BASE_URL` | No | — | Langfuse host URL |

### Mode Switching

```bash
# Development (no API calls):
USE_CACHE=true
CAMPAIGNX_API_BASE_URL=http://localhost:4010

# Production (live API):
USE_CACHE=false
CAMPAIGNX_API_BASE_URL=https://campaignx.inxiteout.ai
```

---

## How It Works

### 1. Brief Submission
The user pastes a natural-language marketing brief (e.g., "Promote XDeposit Fixed Deposit to all customers, highlight 1% better returns..."). The Brief Parser converts it into a structured object.

### 2. Customer Segmentation
1,000 real customers are fetched (or loaded from cache) and split into 5 micro-segments based on age, gender, and income. Each segment gets tailored strategy notes, psychological hooks, and recommended tones.

### 3. A/B Strategy & Creative
For each segment, the Strategy Agent designs 2 variants with distinct tones. The Creative Agent writes compliant email HTML, then runs:
- **Banned-word scan** → auto-regenerates if violations found
- **HTML deduplication** → removes `"phrase <strong>phrase</strong>"` patterns
- **Offer filtering** → senior offers only in senior emails

### 4. Human Approval
The graph pauses. The dashboard shows all 10 variants (2 per segment). The human can approve or reject with feedback.

### 5. Execution & Measurement
On approval, each segment's customers are split 50/50. Campaigns are sent via the live API. After delivery, the Metrics Agent fetches per-customer EO (Email Opened) and EC (Email Clicked) data and computes rates.

### 6. Optimization Loop
The Analytics Agent identifies per-segment winners using composite scores `(0.7 × click_rate + 0.3 × open_rate)`. If there's >5% improvement over the previous iteration, the loop continues (up to 3 iterations).

### 7. Final Send
When optimization ends, the **Final Send** node fires: it sends ONLY the winning variant to ALL customers in each segment. This maximizes the total EO=Y + EC=Y count for scoring.

---

## Team

**Team Four Musketeers** — IIT Mandi

Built for **FrostHack XPECTO 2026**, the flagship hackathon at IIT Mandi.

---

<div align="center">
<sub>Built with LangGraph, Groq, FastAPI, and React</sub>
</div>
