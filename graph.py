from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from models import CampaignState
from tools.discovery import load_openapi_tools_node
from agents.brief_parser import brief_parser_node
from agents.profiler import customer_profiling_node

def strategy_node(state: CampaignState) -> dict:
    print("🤖 Agent: Planning strategy...")
    return {}

def creative_node(state: CampaignState) -> dict:
    print("🤖 Agent: Generating email content...")
    return {}

def hitl_interrupt_node(state: CampaignState) -> dict:
    # This node doesn't do much; the magic happens because LangGraph pauses BEFORE it.
    print("👨‍💻 HITL Node: Human action received!")
    return {}

def execution_node(state: CampaignState) -> dict:
    print("🤖 Agent: Executing campaign...")
    return {}

def metrics_fetcher_node(state: CampaignState) -> dict:
    print("🤖 Agent: Fetching metrics...")
    return {}

def analytics_node(state: CampaignState) -> dict:
    print("🤖 Agent: Analyzing results and optimizing...")
    return {"iteration_count": state.get("iteration_count", 0) + 1}

def error_correction_node(state: CampaignState) -> dict:
    print("🤖 Agent: Correcting API error...")
    return {}

# --- Routing Functions ---
def route_after_hitl(state: CampaignState) -> str:
    status = state.get("hitl_status", "pending")
    if status == "approved":
        return "execute"
    elif status == "rejected":
        return "regenerate"
    return "execute"  # default

def route_after_analysis(state: CampaignState) -> str:
    iteration = state.get("iteration_count", 0)
    max_iter = state.get("max_iterations", 3)
    if state.get("should_continue_optimization", False) and iteration < max_iter:
        return "optimize"
    return "complete"

def route_on_api_error(state: CampaignState) -> str:
    if state.get("api_error_log") and len(state.get("api_error_log", [])) > 0:
        return "error"
    return "success"

# --- Graph Builder ---
def build_campaign_graph():
    builder = StateGraph(CampaignState)

    # Add all nodes
    builder.add_node("load_tools", load_openapi_tools_node)
    builder.add_node("parse_brief", brief_parser_node)
    builder.add_node("profile_customers", customer_profiling_node)
    builder.add_node("plan_strategy", strategy_node)
    builder.add_node("generate_content", creative_node)
    builder.add_node("hitl_approval", hitl_interrupt_node)
    builder.add_node("execute_campaign", execution_node)
    builder.add_node("fetch_metrics", metrics_fetcher_node)
    builder.add_node("analyze_optimize", analytics_node)
    builder.add_node("error_correction", error_correction_node)

    # Entry point
    builder.set_entry_point("load_tools")

    # Sequential edges
    builder.add_edge("load_tools", "parse_brief")
    builder.add_edge("parse_brief", "profile_customers")
    builder.add_edge("profile_customers", "plan_strategy")
    builder.add_edge("plan_strategy", "generate_content")
    builder.add_edge("generate_content", "hitl_approval")

    # HITL conditional edge
    builder.add_conditional_edges(
        "hitl_approval",
        route_after_hitl,
        {
            "execute": "execute_campaign",
            "regenerate": "generate_content",
        }
    )

    # Post-execution
    builder.add_edge("execute_campaign", "fetch_metrics")
    builder.add_edge("fetch_metrics", "analyze_optimize")

    # Optimization loop conditional
    builder.add_conditional_edges(
        "analyze_optimize",
        route_after_analysis,
        {
            "optimize": "plan_strategy", 
            "complete": END,
        }
    )

    # Error edge
    builder.add_conditional_edges(
        "execute_campaign",
        route_on_api_error,
        {
            "success": "fetch_metrics",
            "error": "error_correction",
        }
    )
    builder.add_edge("error_correction", "execute_campaign")

    # Compile with checkpointer for HITL
    memory = MemorySaver()
    return builder.compile(
        checkpointer=memory,
        interrupt_before=["hitl_approval"]
    )