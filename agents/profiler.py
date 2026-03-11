import os
import random
from typing import List
from models import CampaignState, CustomerProfile, MicroSegment
from tools.discovery import get_loaded_tools

def _generate_dummy_cohort() -> List[CustomerProfile]:
    random.seed(42)
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
            location="India",
            monthly_income=random.randint(30000, 800000),
            credit_score=random.randint(300, 850),
            app_installed=random.choice(["Y", "N"]),
        ))
    return cohort

def _map_api_customer(c: dict) -> CustomerProfile:
    """
    Maps the live CampaignX API response fields to our CustomerProfile model.
    API uses capitalized keys and full strings (Male/Female, Y/N).
    """
    return CustomerProfile(
        customer_id=c.get("customer_id"),
        age=c.get("Age"),
        gender="F" if c.get("Gender", "").lower() == "female" else "M",
        status="active" if c.get("Existing Customer", "Y") == "Y" else "inactive",
        employment=c.get("Occupation", "unknown"),
        location=c.get("City", "India"),
        # Map the rich fields the API provides
        monthly_income=c.get("Monthly_Income"),
        credit_score=c.get("Credit score"),
        app_installed=c.get("App_Installed"),
    )

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

    # Segment 3: High Income Working Age (premium FD audience)
    # Threshold set to 350000 based on actual API data distribution (P75 = ~365K, max ~500K)
    high_income_working = [
        c for c in eligible
        if 25 <= c.age < 60
        and c.monthly_income is not None
        and c.monthly_income > 350000
    ]
    if high_income_working:
        segments.append(MicroSegment(
            segment_id="seg_high_income_working",
            name="High Income Working Age 25-59 (>3.5L/month)",
            customer_ids=[c.customer_id for c in high_income_working],
            strategy_notes="Wealth preservation + tax efficiency. Beat equity volatility pitch.",
            psychological_hook="Guaranteed 1% above market in volatile times — capital safety without sacrificing returns",
            recommended_tone="sophisticated, data-driven, peer-level",
            recommended_send_time="08:00 AM IST"
        ))

    # Segment 4: General Working Age
    # Exclude those already in high_income_working segment
    high_income_ids = set(c.customer_id for c in high_income_working) if high_income_working else set()
    working_age = [
        c for c in eligible
        if 25 <= c.age < 60
        and c.customer_id not in high_income_ids
    ]
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

    # Segment 5: Young Adults 18-24
    # 31.8% of the cohort — cannot be silently dropped
    young_adults = [c for c in eligible if c.age < 25]
    if young_adults:
        segments.append(MicroSegment(
            segment_id="seg_young_adults",
            name="Young Adults 18-24",
            customer_ids=[c.customer_id for c in young_adults],
            strategy_notes="First FD, savings habit building, digital-first. Low ticket entry.",
            psychological_hook="Start your wealth journey early — compounding advantage + higher returns than savings account",
            recommended_tone="casual, aspirational, peer-driven",
            recommended_send_time="06:00 PM IST"
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
        full_cohort = [_map_api_customer(c) for c in raw_customers]
        print(f"✅ Fetched {len(full_cohort)} customers from LIVE API.")
    
    # Segment them based on the parsed brief
    include_inactive = state["parsed_brief"].include_inactive if state["parsed_brief"] else False
    active_segments = segment_cohort(full_cohort, include_inactive)
    
    for seg in active_segments:
        print(f"  -> Created Segment: {seg.name} ({len(seg.customer_ids)} customers)")
        
    return {
        "full_cohort": full_cohort,
        "active_segments": active_segments
    }