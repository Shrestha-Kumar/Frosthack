from models import CampaignState
from tools.discovery import get_loaded_tools
from datetime import datetime, timedelta

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
            
        # Convert recommended "10:00 AM IST" to a future date in API format (DD:MM:YY HH:MM:SS)
        # For hackathon purposes, we schedule it for tomorrow at the requested hour
        # Safely convert "07:00 PM IST" to 24-hour format "19:00:00"
        raw_time = segment.recommended_send_time
        time_parts = raw_time.split(" ")
        time_str = time_parts[0]
        
        if "PM" in raw_time and not time_str.startswith("12"):
            h, m = time_str.split(":")
            time_str = f"{int(h)+12:02d}:{m}"
        elif "AM" in raw_time and time_str.startswith("12"):
            time_str = f"00:{time_str.split(':')[1]}"

        tomorrow = datetime.now() + timedelta(days=1)
        formatted_send_time = f"{tomorrow.strftime('%d:%m:%y')} {time_str}:00"

        payload = {
            "subject": variant.subject,
            "body": variant.body_html,
            "list_customer_ids": segment.customer_ids,
            "send_time": formatted_send_time 
        }
        
        # Fire the tool!
        response = send_tool.invoke(payload)
        
        if "campaign_id" in response:
            scheduled_ids.append(response["campaign_id"])
            print(f"  -> Scheduled Campaign {response['campaign_id']} for Variant {variant.variant_id}")
        else:
            print(f"  -> API Error: {response}")
            
    return {"scheduled_campaign_ids": scheduled_ids}