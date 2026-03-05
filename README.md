# CampaignX — AI Multi-Agent Marketing System
FrostHack | XPECTO 2026 | InXiteOut @ IIT Mandi

AI agent system for autonomous email campaign management for SuperBFSI.
Built with LangGraph + Gemini 2.0 Flash + FastAPI + Streamlit.

## Setup
pip install -r requirements.txt
cp .env.example .env  # fill in API keys
python -m uvicorn api.main:app --reload
streamlit run ui/app.py
