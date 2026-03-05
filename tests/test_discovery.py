from tools.discovery import load_openapi_tools_node
from models import CampaignState

# Create an empty dummy state to pass to the node
dummy_state = CampaignState(
    raw_brief="", parsed_brief=None, full_cohort=[], active_segments=[],
    current_variants=[], approved_variants=[], scheduled_campaign_ids=[],
    performance_reports=[], hitl_status="not_started", hitl_feedback=None,
    iteration_count=0, max_iterations=3, optimization_history=[],
    should_continue_optimization=True, openapi_spec=None, discovered_tools=[],
    api_error_log=[], messages=[]
)

# Run the node
result = load_openapi_tools_node(dummy_state)

print("✅ OpenAPI Spec Loaded!")
print(f"Discovered {len(result['discovered_tools'])} tools:\n")

for tool in result['discovered_tools']:
    print(f"- Tool Name: {tool.name}")
    print(f"  Endpoint: {tool.method} {tool.endpoint}")
    print(f"  Description: {tool.description}\n")