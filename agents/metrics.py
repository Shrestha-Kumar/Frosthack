import random
from models import CampaignState, PerformanceReport
from tools.discovery import get_loaded_tools
from datetime import datetime, timezone

def _compute_rates_from_report(response: dict) -> tuple:
    """
    The CampaignX report API returns per-customer rows with EO (Email Opened)
    and EC (Email Clicked) as 'Y'/'N' strings. There are NO aggregate
    open_rate/click_rate fields. We must compute them ourselves.

    Returns (open_rate, click_rate) as floats between 0 and 1.
    """
    report_rows = response.get("data", [])
    total = response.get("total_rows", len(report_rows))

    if total == 0 or not report_rows:
        return (0.0, 0.0)

    opened = sum(1 for row in report_rows if row.get("EO") == "Y")
    clicked = sum(1 for row in report_rows if row.get("EC") == "Y")

    open_rate = opened / total
    click_rate = clicked / total
    return (round(open_rate, 4), round(click_rate, 4))

def metrics_fetcher_node(state: CampaignState) -> dict:
    print("🤖 Agent: Fetching performance metrics...")
    tools = get_loaded_tools()
    report_tool = next((t for t in tools if "get_report" in t.name), None)
    
    if not report_tool:
        raise ValueError("Get Report tool not found!")
        
    reports = []
    variants = state.get("current_variants", [])
    campaign_map = state.get("campaign_variant_map", {})

    # Only fetch metrics for THIS iteration's campaigns.
    # campaign_variant_map is overwritten each iteration (no reducer),
    # so its keys are exactly the current iteration's campaign IDs.
    # Do NOT use scheduled_campaign_ids — it accumulates across iterations
    # via operator.add and would cause "No variant found" warnings for
    # campaign IDs from previous iterations.
    for camp_id in campaign_map.keys():
        response = report_tool.invoke({"campaign_id": camp_id})

        # The report API returns per-customer EO/EC rows, not aggregate rates.
        # Compute open_rate and click_rate from the raw row data.
        open_rate, click_rate = _compute_rates_from_report(response)
        
        # The exact hackathon evaluation formula
        composite = (0.7 * click_rate) + (0.3 * open_rate)
        
        # ID-based lookup instead of fragile index position
        variant_id = campaign_map.get(camp_id)
        variant = next((v for v in variants if v.variant_id == variant_id), None)
        
        if variant:
            total_rows = response.get("total_rows", 0)
            reports.append(PerformanceReport(
                campaign_id=camp_id,
                variant_id=variant.variant_id,
                segment_id=variant.segment_id,
                open_rate=open_rate,
                click_rate=click_rate,
                composite_score=composite,
                fetched_at=datetime.now(timezone.utc).isoformat() 
            ))
            
            print(f"  -> Metrics for {variant.variant_id}: Open={open_rate*100:.1f}%, Click={click_rate*100:.1f}%, Score={composite:.4f} (n={total_rows})")
        else:
            print(f"  -> WARNING: No variant found for campaign_id {camp_id}. Skipping.")
        
    return {"performance_reports": reports}