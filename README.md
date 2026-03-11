# 🚀 CampaignX — Autonomous BFSI Marketing System
**Built by Team Four Musketeers for FrostHack XPECTO 2026 @ IIT Mandi**

CampaignX is an end-to-end agentic platform designed for the BFSI (Banking, Financial Services, and Insurance) sector. It utilizes a multi-agent LangGraph architecture to autonomously parse marketing briefs, segment 1,000 real customers into 5 micro-segments, generate optimized A/B test email variants with per-segment personalization, execute campaigns via a live API, and iteratively optimize based on real performance metrics.

## 🏗️ Architecture
The system is built as a **Multi-Agent System (MAS)** with 8 specialized LangGraph nodes:
* **Tool Discovery**: Dynamically parses the OpenAPI spec and creates LangChain `StructuredTool` instances at runtime.
* **Brief Parser Agent**: Converts natural language briefs into structured `ParsedBrief` objects (product, offers, CTA URL, inactive flag).
* **Customer Profiler Agent**: Fetches 1,000 customers from the live API and segments them into 5 micro-segments:
  - Female Senior Citizens 60+ (special +0.25% offer)
  - Male Senior Citizens 60+ (capital preservation focus)
  - High Income Working Age 25-59 (>3.5L/month, wealth preservation)
  - Working Age Adults 25-59 (portfolio diversification)
  - Young Adults 18-24 (first FD, savings habit building)
* **Strategy Agent**: Creates 2 A/B variants per segment with differentiated tones — enforced programmatically with retry if LLM generates identical tones.
* **Creative Agent**: Generates compliant email HTML with segment-specific context, filtered special offers, banned-word detection, and HTML deduplication post-processing.
* **Execution Agent**: Splits each segment's customers 50/50 for true A/B testing and schedules campaigns via the live API.
* **Metrics Agent**: Fetches per-customer EO/EC data and computes open_rate, click_rate, composite_score (0.7×click + 0.3×open).
* **Analytics Agent**: Per-segment winner identification, programmatic termination logic (stops when <5% improvement or composite ≥ 0.85), and cross-segment tone tracking that prevents false tone banning.

### HITL (Human-in-the-Loop)
The graph pauses at `hitl_approval` before every execution cycle. The user can:
- **Approve** → Executes campaigns and continues to metrics/analytics
- **Reject + Feedback** → Regenerates creative content with the feedback injected into the prompt

### Optimization Loop
```
strategy → creative → HITL → execute → metrics → analytics → (loop if improving, else END)
```
Max 3 iterations. Termination is **programmatic** (not LLM-dependent) to prevent infinite loops.

---

## 🛠️ Tech Stack
### Backend
* **Python 3.11** (Micromamba environment)
* **LangGraph & LangChain**: Multi-agent orchestration with `MemorySaver` checkpointing
* **Groq (Llama 3.3 70B Versatile)**: High-speed inference with Pydantic structured output
* **FastAPI**: Backend API with SQLite thread persistence
* **Langfuse**: Full observability — every LLM call, agent decision, and state transition is traced

### Frontend
* **React + TypeScript**: Premium FinTech-grade dashboard
* **Tailwind CSS & Framer Motion**: Dark theme with smooth animations
* **Recharts**: Real performance metrics visualization (per-segment grouped, with winner badges)
* **Lucide React**: Professional iconography

---

## 🚀 Getting Started

### 1. Prerequisites
* Python 3.11+
* Node.js & npm (or Bun)
* A Groq API Key
* CampaignX API credentials (provided for hackathon)

### 2. Backend Setup
```bash
# Clone the repository
git clone https://github.com/Shrestha-Kumar/Frosthack.git
cd Frosthack

# Install dependencies
pip install -r requirements.txt

# Configure environment (copy .env.example and fill in your keys)
cp .env.example .env

# Start the FastAPI server
uvicorn api.main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
The UI will be available at http://localhost:5173.

---

### 📈 Key Features
* **Dynamic Tool Discovery** — OpenAPI spec parsed at runtime into executable LangChain tools
* **5 Micro-Segments** — Data-driven customer segmentation with income-based thresholds
* **Per-Segment A/B Testing** — True 50/50 customer splits per segment
* **Tone Enforcement** — Programmatic retry ensures A/B variants have distinct tones
* **Segment-Specific Offers** — Emails only mention offers relevant to that audience
* **Compliance** — Banned word detection with automatic regeneration
* **Per-Segment Analytics** — Winners identified per segment, not globally
* **Smart Termination** — Programmatic stop conditions prevent infinite loops
* **Cross-Segment Tone Tracking** — Tones that win in one segment aren't banned globally
* **Self-Healing Error Handler** — Retries API failures with exponential backoff, caps at 3 retries
* **Full Observability** — Langfuse tracing for every agent decision
* **HITL Approval** — Human review before every execution cycle
