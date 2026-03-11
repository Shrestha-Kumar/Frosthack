import os
import json
from langchain_groq import ChatGroq
from pydantic import BaseModel
from typing import List
from models import CampaignState, EmailVariant

class VariantStrategy(BaseModel):
    variant_id: str
    segment_id: str
    tone: str
    has_emoji: bool
    emoji_positions: List[str]
    url_included: bool
    url_position: str
    bold_elements: List[str]
    italic_elements: List[str]
    strategy_explanation: str

class SegmentStrategyPlan(BaseModel):
    variants: List[VariantStrategy]

llm = ChatGroq(
    model="llama-3.3-70b-versatile", 
    temperature=0.2, # slight variance for A/B testing ideas
    api_key=os.getenv("GROQ_API_KEY")
)

structured_llm = llm.with_structured_output(SegmentStrategyPlan)

def strategy_node(state: CampaignState) -> dict:
    print("🤖 Agent: Planning A/B strategy for segments...")
    
    all_planned_variants = []
    
    # Check if this is a regeneration run with human feedback
    feedback = state.get("hitl_feedback")
    feedback_instruction = ""
    if feedback and state.get("hitl_status") == "rejected":
        feedback_instruction = f"\n        CRITICAL HUMAN FEEDBACK FROM PREVIOUS RUN (MUST FOLLOW STRICTLY):\n        \"{feedback}\"\n        Adjust your strategy to explicitly satisfy this feedback."
    
    # Optimization loop memory with structured fields
    history = state.get("optimization_history", [])
    history_context = ""
    if history:
        last = history[-1]
        # Use structured fields for specific actionable guidance
        winning_tones = getattr(last, 'winning_tones', [])
        losing_tones = getattr(last, 'losing_tones', [])
        winning_elements = getattr(last, 'winning_elements', [])

        history_context = f"""
        PREVIOUS ITERATION RESULT — BUILD ON THIS SPECIFICALLY:
        General insight: {last.insight}

        What worked (use these as your Variant 1 baseline):
          - Winning tones: {winning_tones}
          - Winning email elements: {winning_elements}

        What failed (do NOT repeat in Variant 2):
          - Losing tones: {losing_tones}

        Segments that need improvement: {last.segments_retargeted}

        MANDATORY RULES FOR THIS ITERATION:
        - Variant 1 must use one of the winning tones listed above.
        - Variant 2 must test a completely different angle from what failed.
        - Do NOT generate the same tone pair as the previous iteration.
        - Be specific about what element you are testing differently.
        """

    for segment in state.get("active_segments", []):
        prompt = f"""
        You are a digital marketing strategist for an Indian BFSI company.
        Design an A/B testing strategy (2 variants) for this specific customer segment.
        
        Segment Name: {segment.name}
        Strategy Notes: {segment.strategy_notes}
        Psychological Hook: {segment.psychological_hook}
        Recommended Tone: {segment.recommended_tone}
        
        {history_context}
        
        CRITICAL RULES:
        - Generate exactly 2 variant strategies for this segment.
        - Variant 1 should be a safe, standard approach based on the recommended tone.
        - Variant 2 should test a specifically different angle from Variant 1.
        - CTA URL must be included in both.
        - Seniors should have minimal to no emojis. Working age can have 1-2.
        {feedback_instruction}
        
        Return the structured plan.
        """
        
        plan = structured_llm.invoke(prompt)
        
        # Convert the strategy plans into draft EmailVariants (leaving subject/body empty for the Creative Agent)
        for i, vs in enumerate(plan.variants):
            draft_variant = EmailVariant(
                variant_id=f"{segment.segment_id}_v{i+1}",
                segment_id=segment.segment_id,
                subject="", # Creative agent will fill this
                body_html="", # Creative agent will fill this
                tone=vs.tone,
                has_emoji=vs.has_emoji,
                emoji_positions=vs.emoji_positions,
                url_included=vs.url_included,
                url_position=vs.url_position,
                bold_elements=vs.bold_elements,
                italic_elements=vs.italic_elements
            )
            all_planned_variants.append(draft_variant)
            print(f"  -> Planned Variant {draft_variant.variant_id} for {segment.name} (Tone: {draft_variant.tone})")
            
    return {"current_variants": all_planned_variants}