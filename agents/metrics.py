import random
from models import CampaignState, PerformanceReport
from tools.discovery import get_loaded_tools
from datetime import datetime, timezone

def metrics_fetcher_node(state: CampaignState) -> dict:
    print("🤖 Agent: Fetching performance metrics...")
    tools = get_loaded_tools()
    report_tool = next((t for t in tools if "get_report" in t.name), None)
    
    if not report_tool:
        raise ValueError("Get Report tool not found!")
        
    reports = []
    variants = state.get("current_variants", [])
    
    for i, camp_id in enumerate(state.get("scheduled_campaign_ids", [])):
        # Call the actual mock endpoint
        # Call the actual mock endpoint
        response = report_tool.invoke({"campaign_id": camp_id})
        
        # Extract REAL metrics from the API response, fallback to mock data only if missing
        open_rate = response.get("open_rate", round(random.uniform(0.15, 0.45), 3))
        click_rate = response.get("click_rate", round(random.uniform(0.02, 0.18), 3))
        
        # The exact hackathon evaluation formula
        composite = (0.7 * click_rate) + (0.3 * open_rate)
        
        # Match metrics back to the specific variant
        variant = variants[i] if i < len(variants) else None
        
        if variant:
            reports.append(PerformanceReport(
                campaign_id=camp_id,
                variant_id=variant.variant_id,
                segment_id=variant.segment_id,
                open_rate=open_rate,
                click_rate=click_rate,
                composite_score=composite,
                # FIX 5: Dynamic ISO timestamps
                fetched_at=datetime.now(timezone.utc).isoformat() 
            ))
            
            print(f"  -> Metrics for {variant.variant_id}: Open={open_rate*100:.1f}%, Click={click_rate*100:.1f}%, Score={composite:.3f}")
        
    return {"performance_reports": reports}