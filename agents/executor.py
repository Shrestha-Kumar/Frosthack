from models import CampaignState
from tools.discovery import get_loaded_tools
from datetime import datetime, timedelta
from collections import defaultdict

def execution_node(state: CampaignState) -> dict:
    print("🤖 Agent: Executing campaigns (scheduling)...")
    tools = get_loaded_tools()
    
    # Dynamically find the send campaign tool
    send_tool = next((t for t in tools if "send_campaign" in t.name), None)
    if not send_tool:
        raise ValueError("Send Campaign tool not found! Did discovery run?")
        
    # DO NOT read from state — scheduled_campaign_ids uses operator.add reducer,
    # so LangGraph will merge our return with existing state automatically.
    # Reading + appending + returning would cause double-accumulation.
    new_campaign_ids = []
    
    # Always start with an empty error list so old errors are wiped out
    current_errors = []
    # Track campaign_id -> variant_id mapping for safe metric attribution
    campaign_map = {}
    
    # --- A/B Test Customer Splitting ---
    # Group variants by segment so we can split each segment's customers 50/50.
    # Without this split, both variants go to the SAME customers and the API
    # returns identical deterministic EO/EC values, making A/B testing meaningless.
    segment_variants = defaultdict(list)
    for variant in state.get("current_variants", []):
        segment_variants[variant.segment_id].append(variant)

    for segment in state.get("active_segments", []):
        variants_for_seg = segment_variants.get(segment.segment_id, [])
        if not variants_for_seg:
            continue
        
        # Split customer list for A/B testing
        customer_ids = segment.customer_ids
        midpoint = len(customer_ids) // 2
        
        # If only 1 variant (shouldn't happen, but safe), give it all customers
        if len(variants_for_seg) == 1:
            splits = [customer_ids]
        else:
            # v1 gets first half, v2 gets second half
            splits = [customer_ids[:midpoint], customer_ids[midpoint:]]
        
        for idx, variant in enumerate(variants_for_seg):
            # Each variant gets its own split of the customer list
            target_customers = splits[min(idx, len(splits) - 1)]
            
            # Safe time parsing with a fallback to prevent crashes
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
                "list_customer_ids": target_customers,
                "send_time": formatted_send_time 
            }
            
            try:
                # Fire the tool!
                response = send_tool.invoke(payload)
                
                if "campaign_id" in response:
                    camp_id = response["campaign_id"]
                    new_campaign_ids.append(camp_id)
                    campaign_map[camp_id] = variant.variant_id  # Store mapping
                    print(f"  -> Scheduled Campaign {camp_id} for Variant {variant.variant_id} ({len(target_customers)} customers)")
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
            
    # Return only NEW IDs (operator.add in state will merge with existing)
    return {
        "scheduled_campaign_ids": new_campaign_ids,
        "api_error_log": current_errors,
        "campaign_variant_map": campaign_map
    }