from dotenv import load_dotenv
load_dotenv()

# --- START: SILENCE LANGGRAPH WARNINGS ---
import warnings
import logging

# Aggressively filter the exact warning messages
warnings.filterwarnings("ignore", message=".*Deserializing unregistered type.*")
warnings.filterwarnings("ignore", message=".*allowed_msgpack_modules.*")
warnings.filterwarnings("ignore", module="langgraph.*")

# Silence the specific LangGraph internal loggers causing the spam
logging.getLogger("langgraph.checkpoint").setLevel(logging.ERROR)
logging.getLogger("langgraph.checkpoint.serde").setLevel(logging.ERROR)
logging.getLogger("langgraph.checkpoint.serde.msgpack").setLevel(logging.ERROR)
# --- END: SILENCE LANGGRAPH WARNINGS ---

from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import uuid
import time
import sqlite3
from graph import build_campaign_graph
from langfuse.langchain import CallbackHandler

langfuse_handler = CallbackHandler()

from fastapi.middleware.cors import CORSMiddleware

DB_PATH = "campaignx_threads.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS threads (
            thread_id TEXT PRIMARY KEY,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'running'
        )
    """)
    conn.commit()
    conn.close()

def save_thread(thread_id: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR IGNORE INTO threads (thread_id) VALUES (?)",
        (thread_id,)
    )
    conn.commit()
    conn.close()

def update_thread_status(thread_id: str, status: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE threads SET status=? WHERE thread_id=?",
        (status, thread_id)
    )
    conn.commit()
    conn.close()

def recover_graph_if_needed(thread_id: str) -> bool:
    """
    If thread_id is known in DB but not in active_graphs
    (e.g. after a server restart), rebuild the graph object.
    """
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT thread_id FROM threads WHERE thread_id=?",
        (thread_id,)
    ).fetchone()
    conn.close()

    if row and thread_id not in active_graphs:
        graph = build_campaign_graph()
        active_graphs[thread_id] = graph
        print(f"  -> Recovered graph for thread {thread_id} after restart.")
        return True
    return False

app = FastAPI(
    title="CampaignX Backend",
    openapi_url="/openapi.json", 
    docs_url="/docs"
)

init_db()

# Add this CORS middleware block so Lovable can connect!
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def health_check():
    """Simple health check for the frontend to verify the API is online."""
    return {"status": "online", "message": "CampaignX API is running"}

# In-memory registry
active_graphs = {}

class RejectRequest(BaseModel):
    feedback: str

class CampaignStartRequest(BaseModel):
    brief: str

def run_graph_until_interrupt(graph, config, brief):
    # Inject Langfuse into the config
    config["callbacks"] = [langfuse_handler]
    
    graph.invoke(
        {
            "raw_brief": brief,
            "max_iterations": 3,
            "should_continue_optimization": False,
            "iteration_count": 0,
            # Initialize all fields that need non-None defaults
            "api_retry_count": 0,
            "campaign_variant_map": {},
            "best_variant_ids": {},
            "approved_variants": [],
            "messages": [],
            "api_error_log": [],
        },
        config=config
    )

def resume_graph(graph, config):
    # Inject Langfuse into the config
    config["callbacks"] = [langfuse_handler]
    graph.invoke(None, config=config)

@app.post("/campaign/start")
async def start_campaign(req: CampaignStartRequest, background_tasks: BackgroundTasks):
    thread_id = f"camp_{int(time.time())}"
    graph = build_campaign_graph()
    active_graphs[thread_id] = graph
    save_thread(thread_id)
    config = {"configurable": {"thread_id": thread_id}}
    background_tasks.add_task(run_graph_until_interrupt, graph, config, req.brief)
    return {"thread_id": thread_id, "status": "started"}

@app.get("/campaign/{thread_id}/state")
async def get_campaign_state(thread_id: str):
    recover_graph_if_needed(thread_id)
    if thread_id not in active_graphs:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    config = {"configurable": {"thread_id": thread_id}}
    state = active_graphs[thread_id].get_state(config)
    
    # NEW: Properly determine if the graph is completely finished
    if not state.next:
        current_status = "completed"
    elif state.next[0] == "hitl_approval":
        current_status = "awaiting_approval"
    else:
        current_status = "running"
    
    return {
        "status": current_status,
        "thread_id": thread_id,
        "next_node": state.next,
        "iteration_count": state.values.get("iteration_count", 0),
        "should_continue": state.values.get("should_continue_optimization", False),
        "data": {
            "current_variants": [v.model_dump() for v in state.values.get("current_variants", [])],
            "active_segments": [s.model_dump() for s in state.values.get("active_segments", [])],
            "performance_reports": [r.model_dump() for r in state.values.get("performance_reports", [])],
            "optimization_history": [h.model_dump() for h in state.values.get("optimization_history", [])]
        }
    }
    
@app.post("/campaign/{thread_id}/approve")
async def approve_campaign(thread_id: str, background_tasks: BackgroundTasks):
    recover_graph_if_needed(thread_id)
    if thread_id not in active_graphs:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    graph = active_graphs[thread_id]
    config = {"configurable": {"thread_id": thread_id}}
    
    # Update state to approved
    graph.update_state(config, {"hitl_status": "approved"}, as_node="hitl_approval")
    
    # Resume! This is where Day 5 Execution + Metrics + Analytics run
    background_tasks.add_task(resume_graph, graph, config)
    return {"status": "resumed"}

@app.post("/campaign/{thread_id}/reject")
async def reject_campaign(thread_id: str, req: RejectRequest, background_tasks: BackgroundTasks):
    recover_graph_if_needed(thread_id)
    if thread_id not in active_graphs:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    graph = active_graphs[thread_id]
    config = {"configurable": {"thread_id": thread_id}}
    
    # Update state to rejected with feedback
    graph.update_state(config, {"hitl_status": "rejected", "hitl_feedback": req.feedback}, as_node="hitl_approval")
    
    # Resume! Will route back to CreativeAgent
    background_tasks.add_task(resume_graph, graph, config)
    return {"status": "rejected", "message": "Regenerating content based on feedback."}