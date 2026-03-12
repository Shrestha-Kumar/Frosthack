import os
from collections import defaultdict
from langchain_groq import ChatGroq
from pydantic import BaseModel
from typing import List, Dict
from models import CampaignState, OptimizationRecord

class SegmentAnalysis(BaseModel):
    segment_id: str
    winning_variant: str
    winning_tone: str
    losing_tone: str
    insight: str

class OptimizationDecision(BaseModel):
    overall_insight: str
    action_taken: str
    segment_analyses: List[SegmentAnalysis]
    variants_changed: List[str]
    segments_retargeted: List[str]
    winning_elements: List[str]

# Analytics needs 70B for reliable nested structured output (List[SegmentAnalysis]).
# Called 1-3 times per run (~6K tokens total) — minimal rate-limit impact.
ANALYTICS_MODEL = "llama-3.3-70b-versatile"

llm = ChatGroq(
    model=ANALYTICS_MODEL, 
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

    # --- PER-SEGMENT GROUPING ---
    # Group reports by segment so we compare v1 vs v2 WITHIN each segment,
    # not picking a single global winner across all segments.
    segment_reports = defaultdict(list)
    for r in reports:
        segment_reports[r.segment_id].append(r)
    
    # Build per-segment performance data for the LLM
    per_segment_data = {}
    for seg_id, seg_reports in segment_reports.items():
        per_segment_data[seg_id] = [
            {
                "variant_id": r.variant_id,
                "click_rate_pct": round(r.click_rate * 100, 1),
                "open_rate_pct": round(r.open_rate * 100, 1),
                "composite_score": round(r.composite_score, 4),
                "tone": variants_map[r.variant_id].tone if r.variant_id in variants_map else "unknown",
                "has_emoji": variants_map[r.variant_id].has_emoji if r.variant_id in variants_map else None,
                "bold_elements": variants_map[r.variant_id].bold_elements if r.variant_id in variants_map else [],
                "subject_preview": variants_map[r.variant_id].subject[:60] if r.variant_id in variants_map else ""
            }
            for r in seg_reports
        ]

    # Calculate best composite from PREVIOUS iteration for degradation detection
    prev_best = None
    if prev_reports:
        prev_best = max(r.composite_score for r in prev_reports)

    current_best = max([r.composite_score for r in reports], default=0)

    prompt = f"""
    You are a marketing analytics AI for SuperBFSI.
    We just completed Iteration {iteration} of our A/B test.
    
    CRITICAL CONTEXT: The hackathon scores us on TOTAL 'EC=Y' + 'EO=Y' count
    across ALL 1000 customers. The winning variant per segment will be sent
    to ALL customers in that segment on the final iteration (winner-take-all).
    So picking the right winner PER SEGMENT is critical for maximizing score.
    
    Evaluation Formula: composite_score = (0.7 * click_rate) + (0.3 * open_rate)
    
    Performance data GROUPED BY SEGMENT (compare v1 vs v2 WITHIN each segment):
    {per_segment_data}
    
    Analyze the results:
    1. For EACH segment, identify which variant won by composite_score.
       Use the FULL variant_id (e.g. "seg_young_adults_v2", NOT just "v2").
    2. For EACH segment, write a SPECIFIC insight about WHY that variant won —
       reference the tone, emoji usage, subject line preview, and bold elements.
       Do NOT just say "higher click rate." Explain what EMAIL CHARACTERISTIC
       likely drove the difference for THAT specific audience.
    3. For EACH segment, record the winning_tone and losing_tone.
       A tone that wins for seniors may lose for young adults — track separately.
    4. List winning_elements — specific email features that correlated with
       higher scores across segments (e.g. ["no_emoji", "bold_return_rate"]).
    5. List segments_retargeted — segments where the margin between v1 and v2
       was very small (< 0.05 composite difference) and need better testing.
    
    Return the structured OptimizationDecision with a segment_analyses entry
    for each segment.
    """
    
    decision = structured_llm.invoke(prompt)
    
    # --- PROGRAMMATIC TERMINATION LOGIC ---
    # Do NOT trust the LLM for should_continue — calculate it ourselves.
    should_continue = True
    
    if iteration == 0:
        # First iteration: always continue (need baseline comparison)
        should_continue = True
        termination_reason = "first iteration — establishing baseline"
    else:
        if prev_best is not None and prev_best > 0:
            improvement = (current_best - prev_best) / prev_best
            if improvement < 0.05:
                # Less than 5% improvement (or degradation) → stop
                should_continue = False
                termination_reason = f"insufficient improvement ({improvement*100:.1f}% < 5% threshold)"
            elif current_best >= 0.85:
                # Already at high performance → stop
                should_continue = False
                termination_reason = f"high performance reached ({current_best:.4f} >= 0.85)"
            else:
                should_continue = True
                termination_reason = f"improvement detected ({improvement*100:.1f}%)"
        else:
            # No previous data to compare → continue
            should_continue = True
            termination_reason = "no previous baseline"
    
    print(f"  -> Termination check: {termination_reason} → should_continue={should_continue}")
    
    # --- EXTRACT PER-SEGMENT TONES ---
    # Aggregate winning/losing tones from per-segment analyses
    winning_tones = []
    losing_tones = []
    for sa in decision.segment_analyses:
        if sa.winning_tone and sa.winning_tone not in winning_tones:
            winning_tones.append(sa.winning_tone)
        if sa.losing_tone and sa.losing_tone not in losing_tones:
            # Only mark as losing if it didn't WIN in any other segment
            losing_tones.append(sa.losing_tone)
    
    # Remove tones that appear in BOTH winning and losing
    # (a tone can win for one segment but lose for another — don't ban it globally)
    cross_winning_losers = set(winning_tones) & set(losing_tones)
    if cross_winning_losers:
        losing_tones = [t for t in losing_tones if t not in cross_winning_losers]
        print(f"  -> Tones winning in some segments, losing in others (kept): {cross_winning_losers}")
    
    opt_record = OptimizationRecord(
        iteration=iteration,
        insight=decision.overall_insight,
        action_taken=decision.action_taken,
        variants_changed=decision.variants_changed,
        segments_retargeted=decision.segments_retargeted,
        winning_tones=winning_tones,
        losing_tones=losing_tones,
        winning_elements=decision.winning_elements
    )
    
    print(f"  -> Insight: {decision.overall_insight}")
    print(f"  -> Per-segment winners: {[(sa.segment_id, sa.winning_variant, sa.winning_tone) for sa in decision.segment_analyses]}")
    print(f"  -> Winning tones (aggregated): {winning_tones}")
    print(f"  -> Losing tones (filtered): {losing_tones}")
    print(f"  -> Should Continue: {should_continue}")
    
    # --- BUILD BEST VARIANT MAP (ACCUMULATE) ---
    # Carry forward winners from previous iterations, then update with
    # this iteration's results. Since best_variant_ids has no reducer
    # (overwrites), we must merge manually to avoid losing previous winners.
    best_variant_ids = dict(state.get("best_variant_ids", {}))
    
    # Build a set of all valid full variant IDs for normalization
    valid_variant_ids = {v.variant_id for v in state.get("current_variants", [])}
    
    # Update with this iteration's per-segment winners from the LLM
    for sa in decision.segment_analyses:
        winner_id = sa.winning_variant
        
        # Normalize short-form IDs (e.g. "v2") to full IDs (e.g. "seg_young_adults_v2")
        if winner_id not in valid_variant_ids:
            # Try to reconstruct: segment_id + "_" + winner_id
            candidate = f"{sa.segment_id}_{winner_id}"
            if candidate in valid_variant_ids:
                print(f"  -> Normalized variant ID: '{winner_id}' → '{candidate}'")
                winner_id = candidate
            else:
                # Try matching by suffix (e.g. "v2" matches "seg_young_adults_v2")
                matches = [vid for vid in valid_variant_ids if vid.endswith(f"_{winner_id}") and vid.startswith(sa.segment_id)]
                if matches:
                    winner_id = matches[0]
                    print(f"  -> Normalized variant ID: '{sa.winning_variant}' → '{winner_id}'")
                else:
                    print(f"  -> ⚠️  Could not normalize variant ID '{winner_id}' for {sa.segment_id}")
        
        best_variant_ids[sa.segment_id] = winner_id
    
    # ENSURE every active segment has a winner — even if the LLM didn't
    # produce a segment_analysis for it (e.g. identical mock scores).
    # Default to v1 for any segment without an explicit winner.
    for seg in state.get("active_segments", []):
        if seg.segment_id not in best_variant_ids:
            # Pick the first variant for this segment as default winner
            seg_variants = [v for v in state.get("current_variants", []) if v.segment_id == seg.segment_id]
            if seg_variants:
                best_variant_ids[seg.segment_id] = seg_variants[0].variant_id
                print(f"  -> Default winner for {seg.segment_id}: {seg_variants[0].variant_id} (no LLM analysis)")
    
    print(f"  -> Best variant map for winner-take-all: {best_variant_ids}")
    
    return {
        "optimization_history": [opt_record],
        "should_continue_optimization": should_continue,
        "iteration_count": iteration + 1,
        "best_variant_ids": best_variant_ids
    }