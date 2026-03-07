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
        
    scheduled_ids = state.get("scheduled_campaign_ids", [])
    
    # THE FIX: Always start with an empty error list so old errors are wiped out!
    current_errors = []
    
    # Iterate through our generated variants and "send" them
    for variant in state.get("current_variants", []):
        # Match the variant to its target segment to get the customer IDs
        segment = next((s for s in state["active_segments"] if s.segment_id == variant.segment_id), None)
        if not segment:
            continue
            
        # FIX 6: Safe time parsing with a fallback to prevent crashes
        try:
            raw_time = segment.recommended_send_time
            time_parts = raw_time.split(" ")
            time_str = time_parts[0]
            
            if "PM" in raw_time and not time_str.startswith("12"):
                h, m = time_str.split(":")
                time_str = f"{int(h)+12:02d}:{m}"
            elif "AM" in raw_time and time_str.startswith("12"):
                time_str = f"00:{time_str.split(':')[1]}"
        except Exception:
            time_str = "10:00"  # safe default: 10 AM

        tomorrow = datetime.now() + timedelta(days=1)
        formatted_send_time = f"{tomorrow.strftime('%d:%m:%y')} {time_str}:00"

        payload = {
            "subject": variant.subject,
            "body": variant.body_html,
            "list_customer_ids": segment.customer_ids,
            "send_time": formatted_send_time 
        }
        
        try:
            # Fire the tool!
            response = send_tool.invoke(payload)
            
            if "campaign_id" in response:
                scheduled_ids.append(response["campaign_id"])
                print(f"  -> Scheduled Campaign {response['campaign_id']} for Variant {variant.variant_id}")
            else:
                # The tool returned an error dictionary from the mock API
                error_msg = f"API Error for Variant {variant.variant_id}: {response}"
                print(f"  -> {error_msg}")
                current_errors.append(error_msg)
                
        except Exception as e:
            # Catch any hard crashes (like network disconnections)
            error_msg = f"System Error for Variant {variant.variant_id}: {str(e)}"
            print(f"  -> {error_msg}")
            current_errors.append(error_msg)
            
    # Return BOTH the successful IDs and the error log so the LangGraph can route appropriately
    return {
        "scheduled_campaign_ids": scheduled_ids,
        "api_error_log": current_errors
    }