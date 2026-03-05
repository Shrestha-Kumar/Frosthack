# 🚀 CampaignX — Autonomous BFSI Marketing System
**Built by Team Four Musketeers for FrostHack 2026** [cite: 2026-02-27]

CampaignX is an end-to-end agentic platform designed for the BFSI (Banking, Financial Services, and Insurance) sector. It utilizes a multi-agent LangGraph architecture to autonomously parse marketing briefs, segment customers, generate optimized A/B test email variants, and execute campaigns via a mock API with real-time performance tracking.

## 🏗️ Architecture
The system is built as a **Multi-Agent System (MAS)** where specialized agents collaborate:
* **Brief Parser Agent**: Converts natural language into structured campaign requirements.
* **Strategy Agent**: Segments customers based on behavioral data and creates psychological hooks.
* **Creative Agent**: Generates HTML email variants while strictly adhering to compliance (No emojis in subjects, specific font formatting).
* **Execution Agent**: Dynamically discovers API endpoints and schedules campaigns using dynamic Pydantic models.
* **Metrics & Analytics Agent**: Fetches performance data and performs **Thompson Sampling** to optimize future iterations.

---

## 🛠️ Tech Stack
### Backend
* **Python 3.11** (Mamba/Conda environment) [cite: 2026-02-25].
* **LangGraph & LangChain**: Orchestrating agent workflows and state management.
* **FastAPI**: High-performance web framework for the API layer.
* **Groq (Llama 3.3 70B)**: High-speed inference for agent "reasoning."

### Frontend
* **React + TypeScript**: Built with a premium FinTech aesthetic.
* **Tailwind CSS & Framer Motion**: For smooth, high-fidelity UI transitions.
* **Lucide React**: For professional iconography.

---

## 🚀 Getting Started

### 1. Prerequisites
* Python 3.11+
* Node.js & npm (or Bun)
* A Groq API Key

### 2. Backend Setup
```bash
# Clone the repository
git clone [https://github.com/Shrestha-Kumar/Frosthack.git](https://github.com/Shrestha-Kumar/Frosthack.git)
cd Frosthack

# Install dependencies
pip install -r requirements.txt

# Configure environment
# Create a .env file and add:
# GROQ_API_KEY=your_key_here
# CAMPAIGN_API_BASE_URL=[http://127.0.0.1:4010/api/v1](http://127.0.0.1:4010/api/v1)
# CAMPAIGN_API_KEY=frosthack_secret_2026

# Start the FastAPI server
uvicorn api.main:app --reload --port 8000
```

### 3. Mock API Setup (Prism)
```bash
# Run the mock server to simulate the CampaignX API
npx @stoplight/prism-cli mock campaignx_api.json --port 4010
```

### 4. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
The UI will be available at http://localhost:8080 (or 5173).

### 📈 Project Roadmap

* Day 1-2: Environment setup and Tool Discovery. ✅
* Day 3-4: Brief Parsing and Strategy Agents. ✅
* Day 5-6: Multi-loop execution and Performance Metrics. ✅
* Day 7: Lovable React UI Integration and Navigation. ✅
* Day 8: Self-healing Error Correction & Telemetry. 🚧 (In Progress)
