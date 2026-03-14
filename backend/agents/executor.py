import os
from models import CampaignState
from tools.discovery import get_loaded_tools
from datetime import datetime, timedelta
from collections import defaultdict

def _parse_send_time(raw_time: str) -> str:
    """Parse recommended_send_time like '10:00 AM IST' into 24h HH:MM format."""
    try:
        time_parts = raw_time.split(" ")
        time_str = time_parts[0]
        
        if "PM" in raw_time and not time_str.startswith("12"):
            h, m = time_str.split(":")
            time_str = f"{int(h)+12:02d}:{m}"
        elif "AM" in raw_time and time_str.startswith("12"):
            time_str = f"00:{time_str.split(':')[1]}"
        return time_str
    except Exception:
        return "10:00"  # safe default: 10 AM

def _format_send_time(time_str: str = None) -> str:
    """
    Build the send_time string in API format 'DD:MM:YY HH:MM:SS'.

    WHY we ignore `time_str` entirely:
    Segment recommended_send_time values are morning slots (8-10 AM IST).
    When campaigns run in the afternoon, those times are already in the past.
    datetime.now() returns UTC on most servers, so the "roll to tomorrow"
    check fires against UTC clock but the API validates against IST — causing
    422 "send_time cannot be in the past" errors for any morning slot.

    Solution: always schedule 30 minutes from NOW (server local time).
    This is guaranteed future regardless of what time of day the run happens,
    and gives the API enough time to queue the campaign properly.
    """
    from datetime import timezone
    import pytz

    try:
        ist = pytz.timezone("Asia/Kolkata")
        now_ist = datetime.now(ist)
        future_ist = now_ist + timedelta(minutes=30)
        return future_ist.strftime('%d:%m:%y %H:%M:%S')
    except Exception:
        # pytz not installed — fall back to UTC + 5:30 offset manually
        now_utc = datetime.utcnow()
        now_ist = now_utc + timedelta(hours=5, minutes=30)
        future_ist = now_ist + timedelta(minutes=30)
        return future_ist.strftime('%d:%m:%y %H:%M:%S')

def execution_node(state: CampaignState) -> dict:
    print("🤖 Agent: Executing campaigns (scheduling)...")
    tools = get_loaded_tools()
    
    # Dynamically find the send campaign tool
    send_tool = next((t for t in tools if "send_campaign" in t.name), None)
    if not send_tool:
        raise ValueError("Send Campaign tool not found! Did discovery run?")
        
    new_campaign_ids = []
    current_errors = []
    campaign_map = {}
    
    # Group variants by segment
    segment_variants = defaultdict(list)
    for variant in state.get("current_variants", []):
        segment_variants[variant.segment_id].append(variant)

    for segment in state.get("active_segments", []):
        variants_for_seg = segment_variants.get(segment.segment_id, [])
        if not variants_for_seg:
            continue
        
        customer_ids = segment.customer_ids
        time_str = _parse_send_time(segment.recommended_send_time)
        
        # ALWAYS A/B SPLIT during optimization iterations.
        # Winner-take-all is handled ONLY by final_send_node after analytics finishes.
        midpoint = len(customer_ids) // 2
        if len(variants_for_seg) == 1:
            variants_to_send = [(variants_for_seg[0], customer_ids)]
        else:
            variants_to_send = [
                (variants_for_seg[0], customer_ids[:midpoint]),
                (variants_for_seg[1], customer_ids[midpoint:])
            ]
        
        for variant, target_customers in variants_to_send:
            # --- PERSONALIZATION ---
            # Inject customer first name into the email body greeting
            # The API sends individual emails per customer_id, but the body is shared.
            # We personalize with a generic "Dear [First Name]" approach:
            # Since the body is the SAME for all customer_ids in one send_campaign call,
            # we can't do per-customer personalization within a single API call.
            # But we CAN ensure the email content is maximally relevant.
            
            formatted_send_time = _format_send_time(time_str)

            payload = {
                "subject": variant.subject,
                "body": variant.body_html,
                "list_customer_ids": target_customers,
                "send_time": formatted_send_time 
            }
            
            try:
                response = send_tool.invoke(payload)
                
                if "campaign_id" in response:
                    camp_id = response["campaign_id"]
                    new_campaign_ids.append(camp_id)
                    campaign_map[camp_id] = variant.variant_id
                    print(f"  -> [A/B] Campaign {camp_id} for {variant.variant_id} ({len(target_customers)} customers)")
                else:
                    error_msg = f"API Error for Variant {variant.variant_id}: {response}"
                    print(f"  -> {error_msg}")
                    current_errors.append(error_msg)
                    
            except Exception as e:
                error_msg = f"System Error for Variant {variant.variant_id}: {str(e)}"
                print(f"  -> {error_msg}")
                current_errors.append(error_msg)
            
    return {
        "scheduled_campaign_ids": new_campaign_ids,
        "api_error_log": current_errors,
        "campaign_variant_map": campaign_map
    }


def final_send_node(state: CampaignState) -> dict:
    """
    Winner-take-all node: runs ONCE after analytics decides optimisation is done.
    Sends the winning variant to ALL customers in each segment, maximising
    the EC=Y + EO=Y count for hackathon scoring.
    """
    best_variant_ids = state.get("best_variant_ids", {})
    if not best_variant_ids:
        print("⚠️  final_send: No best_variant_ids found — skipping winner send.")
        return {}

    print("🏆 FINAL SEND: Winner-take-all — sending best variant to ALL customers per segment")

    tools = get_loaded_tools()
    send_tool = next((t for t in tools if "send_campaign" in t.name), None)
    if not send_tool:
        raise ValueError("Send Campaign tool not found! Did discovery run?")

    new_campaign_ids = []
    campaign_map = {}

    # Build a variant lookup from the MOST RECENT current_variants
    variant_lookup = {}
    for v in state.get("current_variants", []):
        variant_lookup[v.variant_id] = v

    for segment in state.get("active_segments", []):
        best_vid = best_variant_ids.get(segment.segment_id)
        
        # Fallback chain: best_variant_ids → first variant for this segment
        winner = None
        if best_vid:
            winner = variant_lookup.get(best_vid)
        
        if not winner:
            # No winner ID or winner not in current variants — pick first available
            candidates = [v for v in state.get("current_variants", []) if v.segment_id == segment.segment_id]
            if candidates:
                winner = candidates[0]
                print(f"  -> ⚠️  Fallback for {segment.segment_id}: using {winner.variant_id} (best_vid was {best_vid})")
            else:
                print(f"  -> ⚠️  No variants at all for {segment.segment_id}, skipping")
                continue

        time_str = _parse_send_time(segment.recommended_send_time)
        formatted_send_time = _format_send_time(time_str)

        payload = {
            "subject": winner.subject,
            "body": winner.body_html,
            "list_customer_ids": segment.customer_ids,
            "send_time": formatted_send_time,
        }

        try:
            response = send_tool.invoke(payload)
            if "campaign_id" in response:
                camp_id = response["campaign_id"]
                new_campaign_ids.append(camp_id)
                campaign_map[camp_id] = winner.variant_id
                print(f"  -> [WINNER] Campaign {camp_id} for {winner.variant_id} ({len(segment.customer_ids)} customers)")
            else:
                print(f"  -> API Error for Winner {winner.variant_id}: {response}")
        except Exception as e:
            print(f"  -> System Error for Winner {winner.variant_id}: {e}")

    return {
        "scheduled_campaign_ids": new_campaign_ids,
        "campaign_variant_map": campaign_map,
    }