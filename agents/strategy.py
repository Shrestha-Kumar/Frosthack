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
    url_position: str  # Must be one of: "end", "middle", "early", "early_and_end", "after_header". Do NOT put an actual URL here.
    bold_elements: List[str]
    italic_elements: List[str]
    strategy_explanation: str

class SegmentStrategyPlan(BaseModel):
    variants: List[VariantStrategy]

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

llm = ChatGroq(
    model=GROQ_MODEL, 
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
        base_prompt = f"""
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
        - Variant 2 MUST use a COMPLETELY DIFFERENT tone from Variant 1.
          For example, if V1 is "authoritative, formal", V2 could be "warm, conversational".
          The two variants must NOT share the same primary tone word.
        - CTA URL must be included in both.
        
        SEGMENT-SPECIFIC EMOJI & FORMAT RULES:
        - Senior segments (60+): has_emoji MUST be false. ZERO emojis.
          Senior emails are penalized by the API for any emoji usage.
          url_position MUST be "early_and_end" (twice in the email).
          bold_elements should include the return rate and "Section 80TTB" or "DICGC-insured".
        - Young Adults (18-24): emojis limited to 1-2 max. 
          url_position MUST be "early" (within first 3 lines of body).
          bold_elements should be punchy, action-oriented phrases.
        - Working age / High income: can have 1-2 emojis. Standard URL placement.
        
        URL POSITION FIELD:
        - url_position must be a DESCRIPTOR, not an actual URL.
          Valid values: "end", "middle", "early", "early_and_end", "after_header"
          WRONG: "https://www.example.com/invest" or any URL string.
          CORRECT: "end" or "early_and_end"
        
        BOLD & ITALIC ELEMENTS — CRITICAL:
        - bold_elements and italic_elements MUST be actual customer-facing phrases
          that will appear VERBATIM inside <strong> or <em> tags in the email.
        - They must be real marketing copy a customer would read — NOT abstract
          labels, category names, or internal jargon.
        - WRONG: ["benefits", "CTA", "headline", "strategy_explanation", "peer_level"]
        - WRONG: ["wealth_preservation", "tax_efficiency", "capital_safety"]
        - CORRECT: ["1% higher assured returns", "DICGC-insured safety"]
        - CORRECT: ["Start your wealth journey today", "Section 80TTB tax benefit"]
        - Each element should be 2-8 words of compelling marketing copy.
        
        ANTI-HALLUCINATION RULE:
        - Do NOT reference any offer, bonus, cashback, referral reward, welcome bonus,
          or financial incentive that is NOT in the segment's strategy notes.
        - If the brief does not mention a "₹500 bonus" or "welcome bonus", do NOT invent one.
        - Stick strictly to the product details provided. Invented offers are BFSI compliance violations.
        {feedback_instruction}
        
        Return the structured plan.
        """
        
        # Invoke with retry to enforce tone differentiation between v1 and v2
        plan = structured_llm.invoke(base_prompt)
        
        # --- PROGRAMMATIC TONE ENFORCEMENT ---
        # If both variants have the same tone, re-invoke with stricter instructions.
        if len(plan.variants) >= 2:
            tone_v1 = plan.variants[0].tone.lower().strip()
            tone_v2 = plan.variants[1].tone.lower().strip()
            if tone_v1 == tone_v2:
                print(f"  -> ⚠️  Same tone for both variants in {segment.name}: '{tone_v1}'. Regenerating V2...")
                retry_prompt = base_prompt + f"""

                CRITICAL CORRECTION: Your previous response gave BOTH variants the SAME tone: "{tone_v1}".
                This defeats A/B testing. Variant 2 MUST use a completely different tone.
                Variant 1 tone MUST stay as: "{tone_v1}"
                Variant 2 tone MUST be distinctly different (different primary adjective).
                """
                plan = structured_llm.invoke(retry_prompt)
        
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