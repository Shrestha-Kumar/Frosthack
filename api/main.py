# from fastapi import FastAPI, BackgroundTasks, HTTPException
# from pydantic import BaseModel
# import uuid
# import time
# from graph import build_campaign_graph

# app = FastAPI(title="CampaignX Backend")

# # In-memory dictionary to hold active graph instances
# # (Sufficient for the hackathon demo without needing a separate database instance)
# active_graphs = {}

# class CampaignStartRequest(BaseModel):
#     brief: str

# class RejectRequest(BaseModel):
#     feedback: str

# def _run_graph_background(graph, config, brief):
#     """Runs the initial graph until it hits the HITL interrupt."""
#     graph.invoke(
#         {"raw_brief": brief, "max_iterations": 3, "should_continue_optimization": False},
#         config=config
#     )

# def _resume_graph_background(graph, config):
#     """Resumes the graph after human approval/rejection."""
#     graph.invoke(None, config=config)

# @app.post("/campaign/start")
# async def start_campaign(req: CampaignStartRequest, background_tasks: BackgroundTasks):
#     thread_id = f"campaign_{int(time.time())}_{uuid.uuid4().hex[:6]}"
#     graph = build_campaign_graph()
#     active_graphs[thread_id] = graph

#     config = {"configurable": {"thread_id": thread_id}}

#     # Start the LangGraph execution in a background thread
#     background_tasks.add_task(_run_graph_background, graph, config, req.brief)

#     return {"thread_id": thread_id, "status": "started"}

# @app.get("/campaign/{thread_id}/state")
# async def get_campaign_state(thread_id: str):
#     graph = active_graphs.get(thread_id)
#     if not graph:
#         raise HTTPException(status_code=404, detail="Campaign thread not found")

#     config = {"configurable": {"thread_id": thread_id}}
#     state = graph.get_state(config)

#     if not state.values:
#         return {"status": "initializing"}

#     # Determine the current execution status
#     current_status = "running"
#     if state.next and state.next[0] == "hitl_approval":
#         current_status = "awaiting_approval"
#     elif not state.next:
#         current_status = "complete"

#     return {
#         "status": current_status,
#         "current_variants": [v.dict() for v in state.values.get("current_variants", [])],
#         "active_segments": [s.dict() for s in state.values.get("active_segments", [])],
#         "performance_reports": [r.dict() for r in state.values.get("performance_reports", [])],
#         "optimization_history": [r.dict() for r in state.values.get("optimization_history", [])],
#         "iteration_count": state.values.get("iteration_count", 0)
#     }

# @app.post("/campaign/{thread_id}/approve")
# async def approve_campaign(thread_id: str, background_tasks: BackgroundTasks):
#     graph = active_graphs.get(thread_id)
#     if not graph:
#         raise HTTPException(status_code=404, detail="Campaign thread not found")

#     config = {"configurable": {"thread_id": thread_id}}
    
#     # Update the graph's memory to reflect human approval
#     graph.update_state(config, {"hitl_status": "approved"}, as_node="hitl_approval")
    
#     # Resume the graph (This triggers Day 5's Execution, Metrics, and Analytics nodes)
#     background_tasks.add_task(_resume_graph_background, graph, config)

#     return {"status": "approved", "message": "Campaign approved and scheduling in background."}

# @app.post("/campaign/{thread_id}/reject")
# async def reject_campaign(thread_id: str, req: RejectRequest, background_tasks: BackgroundTasks):
#     graph = active_graphs.get(thread_id)
#     if not graph:
#         raise HTTPException(status_code=404, detail="Campaign thread not found")

#     config = {"configurable": {"thread_id": thread_id}}
    
#     # Update the graph's memory with rejection and feedback
#     graph.update_state(config, {"hitl_status": "rejected", "hitl_feedback": req.feedback}, as_node="hitl_approval")
    
#     # Resume the graph (Will route back to CreativeAgent to regenerate)
#     background_tasks.add_task(_resume_graph_background, graph, config)

#     return {"status": "rejected", "message": "Campaign rejected, regenerating content."}

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
        "data": state.values  # This contains our variants and metrics
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