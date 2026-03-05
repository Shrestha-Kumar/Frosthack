from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import uuid
import time
from graph import build_campaign_graph

app = FastAPI(
    title="CampaignX Backend",
    openapi_url="/openapi.json", # Explicitly set this
    docs_url="/docs"
)

# In-memory registry
active_graphs = {}

class RejectRequest(BaseModel):
    feedback: str

class CampaignStartRequest(BaseModel):
    brief: str

def run_graph_until_interrupt(graph, config, brief):
    # This fires the nodes we built in Day 3 & 4
    graph.invoke(
        {"raw_brief": brief, "max_iterations": 3, "should_continue_optimization": False},
        config=config
    )

def resume_graph(graph, config):
    # This triggers the Day 5 nodes (Execution, Metrics, Analytics)
    graph.invoke(None, config=config)

@app.post("/campaign/start")
async def start_campaign(req: CampaignStartRequest, background_tasks: BackgroundTasks):
    thread_id = f"camp_{int(time.time())}"
    graph = build_campaign_graph()
    active_graphs[thread_id] = graph
    config = {"configurable": {"thread_id": thread_id}}
    background_tasks.add_task(run_graph_until_interrupt, graph, config, req.brief)
    return {"thread_id": thread_id, "status": "started"}

@app.get("/campaign/{thread_id}/state")
async def get_campaign_state(thread_id: str):
    if thread_id not in active_graphs:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    config = {"configurable": {"thread_id": thread_id}}
    state = active_graphs[thread_id].get_state(config)
    
    # Check if we are at the HITL interrupt
    is_awaiting = state.next and state.next[0] == "hitl_approval"
    
    return {
            "status": "awaiting_approval" if is_awaiting else "running",
            "thread_id": thread_id,
            "next_node": state.next,
            "data": {
                "current_variants": [v.model_dump() for v in state.values.get("current_variants", [])],
                "active_segments": [s.model_dump() for s in state.values.get("active_segments", [])],
                "performance_reports": [r.model_dump() for r in state.values.get("performance_reports", [])],
                "optimization_history": [h.model_dump() for h in state.values.get("optimization_history", [])]
            }
        }

@app.post("/campaign/{thread_id}/approve")
async def approve_campaign(thread_id: str, background_tasks: BackgroundTasks):
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
    if thread_id not in active_graphs:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    graph = active_graphs[thread_id]
    config = {"configurable": {"thread_id": thread_id}}
    
    # Update state to rejected with feedback
    graph.update_state(config, {"hitl_status": "rejected", "hitl_feedback": req.feedback}, as_node="hitl_approval")
    
    # Resume! Will route back to CreativeAgent
    background_tasks.add_task(resume_graph, graph, config)
    return {"status": "rejected", "message": "Regenerating content based on feedback."}