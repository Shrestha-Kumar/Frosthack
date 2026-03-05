from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from models import CampaignState
from tools.discovery import load_openapi_tools_node
from agents.brief_parser import brief_parser_node
from agents.profiler import customer_profiling_node
from agents.strategy import strategy_node
from agents.creative import creative_node
from agents.executor import execution_node
from agents.metrics import metrics_fetcher_node
from agents.analytics import analytics_node

def hitl_interrupt_node(state: CampaignState) -> dict:
    # This node doesn't do much; the magic happens because LangGraph pauses BEFORE it.
    print("👨‍💻 HITL Node: Human action received!")
    return {}

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
    # Only route to error if the most recent execution explicitly failed
    latest_error = state.get("latest_api_error")
    if latest_error is not None:
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