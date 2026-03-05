import os
import random
from typing import List
from models import CampaignState, CustomerProfile, MicroSegment
from tools.discovery import get_loaded_tools

def _generate_dummy_cohort() -> List[CustomerProfile]:
    """Generates 50 realistic mock customers for development testing."""
    cohort = []
    for i in range(1, 51):
        age = random.randint(22, 75)
        gender = random.choice(["M", "F"])
        status = random.choice(["active", "active", "active", "inactive"]) # 25% inactive
        
        cohort.append(CustomerProfile(
            customer_id=f"CUST_{i:03d}",
            age=age,
            gender=gender,
            status=status,
            employment="salaried" if 25 <= age < 60 else "retired",
            location="India"
        ))
    return cohort

def segment_cohort(customers: List[CustomerProfile], include_inactive: bool) -> List[MicroSegment]:
    segments = []

    # Filter based on the critical inactive flag
    if include_inactive:
        eligible = customers
    else:
        eligible = [c for c in customers if c.status == "active"]

    # Segment 1: Female Senior Citizens
    female_seniors = [c for c in eligible if c.gender == "F" and c.age >= 60]
    if female_seniors:
        segments.append(MicroSegment(
            segment_id="seg_female_senior",
            name="Female Senior Citizens 60+",
            customer_ids=[c.customer_id for c in female_seniors],
            strategy_notes="Special +0.25% offer applies. Highest conversion potential.",
            psychological_hook="Section 80TTB tax benefit + exclusive premium return",
            recommended_tone="respectful, secure, warm",
            recommended_send_time="10:00 AM IST"
        ))

    # Segment 2: Male Senior Citizens
    male_seniors = [c for c in eligible if c.gender == "M" and c.age >= 60]
    if male_seniors:
        segments.append(MicroSegment(
            segment_id="seg_male_senior",
            name="Male Senior Citizens 60+",
            customer_ids=[c.customer_id for c in male_seniors],
            strategy_notes="Capital preservation focus. RBI/DICGC safety messaging.",
            psychological_hook="Guaranteed returns, government-backed safety",
            recommended_tone="authoritative, formal, trustworthy",
            recommended_send_time="09:00 AM IST"
        ))

    # Segment 3: Working Age
    working_age = [c for c in eligible if 25 <= c.age < 60]
    if working_age:
        segments.append(MicroSegment(
            segment_id="seg_working_age",
            name="Working Age Adults 25-59",
            customer_ids=[c.customer_id for c in working_age],
            strategy_notes="Portfolio diversification, digital convenience, compounding.",
            psychological_hook="Beat market volatility, 1% higher guaranteed return",
            recommended_tone="modern, concise, data-driven",
            recommended_send_time="07:00 PM IST"
        ))

    return segments

def customer_profiling_node(state: CampaignState) -> dict:
    print("🤖 Agent: Fetching cohort and profiling customers...")
    
    # Check if we are in mock mode to use our 50 dummy users
    is_mock_mode = os.getenv("MOCK_MODE", "false").lower() == "true"
    
    if is_mock_mode:
        full_cohort = _generate_dummy_cohort()
        print(f"✅ Generated {len(full_cohort)} realistic dummy customers for testing.")
    else:
        # Real API execution path
        tools = get_loaded_tools()
        cohort_tool = next((t for t in tools if "get_customer_cohort" in t.name), None)
        if not cohort_tool:
            raise ValueError("Cohort API tool not found!")
            
        api_response = cohort_tool.invoke({})
        raw_customers = api_response.get("data", [])
        full_cohort = [CustomerProfile(**c) for c in raw_customers]
        print(f"✅ Fetched {len(full_cohort)} customers from LIVE API.")
    
    # 4. Segment them based on the parsed brief
    include_inactive = state["parsed_brief"].include_inactive if state["parsed_brief"] else False
    active_segments = segment_cohort(full_cohort, include_inactive)
    
    for seg in active_segments:
        print(f"  -> Created Segment: {seg.name} ({len(seg.customer_ids)} customers)")
        
    return {
        "full_cohort": full_cohort,
        "active_segments": active_segments
    }