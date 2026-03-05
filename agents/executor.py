from models import CampaignState
from tools.discovery import get_loaded_tools

def execution_node(state: CampaignState) -> dict:
    print("🤖 Agent: Executing campaigns (scheduling)...")
    tools = get_loaded_tools()
    
    # Dynamically find the send campaign tool
    send_tool = next((t for t in tools if "send_campaign" in t.name), None)
    if not send_tool:
        raise ValueError("Send Campaign tool not found! Did discovery run?")
        
    scheduled_ids = []
    
    # Iterate through our generated variants and "send" them
    for variant in state.get("current_variants", []):
        # Match the variant to its target segment to get the customer IDs
        segment = next((s for s in state["active_segments"] if s.segment_id == variant.segment_id), None)
        if not segment:
            continue
            
        payload = {
            "subject": variant.subject,
            "body": variant.body_html,
            "list_customer_ids": segment.customer_ids,
            "send_time": "25:03:26 10:00:00"  # Specific DD:MM:YY HH:MM:SS format required by API
        }
        
        # Fire the tool!
        response = send_tool.invoke(payload)
        
        if "campaign_id" in response:
            scheduled_ids.append(response["campaign_id"])
            print(f"  -> Scheduled Campaign {response['campaign_id']} for Variant {variant.variant_id}")
        else:
            print(f"  -> API Error: {response}")
            
    return {"scheduled_campaign_ids": scheduled_ids}