import os
from langchain_groq import ChatGroq
from pydantic import BaseModel
from typing import List
from models import CampaignState, OptimizationRecord

class OptimizationDecision(BaseModel):
    insight: str
    action_taken: str
    variants_changed: List[str]
    segments_retargeted: List[str]
    should_continue: bool
    winning_tones: List[str]
    losing_tones: List[str]
    winning_elements: List[str]

llm = ChatGroq(
    model="llama-3.3-70b-versatile", 
    temperature=0.1, 
    api_key=os.getenv("GROQ_API_KEY")
)

structured_llm = llm.with_structured_output(OptimizationDecision)

def analytics_node(state: CampaignState) -> dict:
    print("🤖 Agent: Analyzing results and deciding next steps...")
    
    iteration = state.get("iteration_count", 0)
    all_reports = state.get("performance_reports", [])
    campaign_map = state.get("campaign_variant_map", {})

    # --- CRITICAL: separate current vs previous iteration reports ---
    # performance_reports accumulates via operator.add across iterations.
    # campaign_variant_map is overwritten each iteration (no reducer),
    # so its values are exactly the current iteration's variant IDs.
    current_variant_ids = set(campaign_map.values())
    
    # Current iteration's reports: those whose variant_id is in the current map
    reports = [r for r in all_reports if r.variant_id in current_variant_ids]
    # Previous iterations' reports: everything else
    prev_reports = [r for r in all_reports if r.variant_id not in current_variant_ids]

    # Build a map of variant metadata so we can include email content
    # context alongside metrics — makes insights non-circular
    variants_map = {v.variant_id: v for v in state.get("current_variants", [])}

    perf_data = [
        {
            "variant_id": r.variant_id,
            "segment_id": r.segment_id,
            "click_rate": round(r.click_rate * 100, 1),
            "open_rate": round(r.open_rate * 100, 1),
            "composite_score": round(r.composite_score, 4),
            # Include email characteristics so insight can reference
            # what actually caused the performance difference
            "tone": variants_map[r.variant_id].tone if r.variant_id in variants_map else "unknown",
            "has_emoji": variants_map[r.variant_id].has_emoji if r.variant_id in variants_map else None,
            "bold_elements": variants_map[r.variant_id].bold_elements if r.variant_id in variants_map else [],
            "subject_preview": variants_map[r.variant_id].subject[:60] if r.variant_id in variants_map else ""
        }
        for r in reports
    ]

    # Calculate best composite from PREVIOUS iteration for degradation detection
    prev_best = None
    if prev_reports:
        prev_best = max(r.composite_score for r in prev_reports)

    current_best = max([r.composite_score for r in reports], default=0)

    prompt = f"""
    You are a marketing analytics AI for SuperBFSI.
    We just completed Iteration {iteration} of our A/B test.
    
    Evaluation Formula: composite_score = (0.7 * click_rate) + (0.3 * open_rate)
    
    Performance data (includes email tone and content characteristics):
    {perf_data}
    
    Analyze the results:
    1. Identify the winning variant per segment by composite_score.
    2. Write a SPECIFIC insight about WHY it won — reference the tone, emoji
       usage, subject line preview, and bold elements. Do NOT just say "higher
       click rates caused the win." Explain what EMAIL CHARACTERISTIC likely
       drove the difference.
    3. List the winning tones (e.g. ["authoritative", "formal"]) and losing
       tones (e.g. ["warm", "reassuring"]) based on the data.
    4. List winning_elements — specific email features that correlated with
       higher scores (e.g. ["no_emoji", "bold_return_rate", "urgency_cta"]).
    5. Determine should_continue:
       - Return True ONLY IF the highest composite score is below 0.85
         AND the current best score is at least 5% better than previous best.
       - Return False if performance degraded or improvement < 5%.

    Current best composite: {current_best:.4f}
    Previous best composite: {prev_best if prev_best else 'N/A (first iteration)'}
    
    Return the structured OptimizationDecision.
    """
    
    decision = structured_llm.invoke(prompt)
    
    opt_record = OptimizationRecord(
        iteration=iteration,
        insight=decision.insight,
        action_taken=decision.action_taken,
        variants_changed=decision.variants_changed,
        segments_retargeted=decision.segments_retargeted,
        winning_tones=decision.winning_tones,
        losing_tones=decision.losing_tones,
        winning_elements=decision.winning_elements
    )
    
    print(f"  -> Insight: {decision.insight}")
    print(f"  -> Winning tones: {decision.winning_tones}")
    print(f"  -> Should Continue: {decision.should_continue}")
    
    return {
        "optimization_history": [opt_record],
        "should_continue_optimization": decision.should_continue,
        "iteration_count": iteration + 1
    }