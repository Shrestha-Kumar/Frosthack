import os
import re
from langchain_groq import ChatGroq
from pydantic import BaseModel
from models import CampaignState, EmailVariant

class GeneratedCopy(BaseModel):
    subject: str
    body_html: str

BANNED_WORDS = [
    "free", "guarantee", "act now", "limited time",
    "click here", "buy now", "urgent", "expires today",
    "don't miss", "last chance"
]

llm = ChatGroq(
    model="llama-3.3-70b-versatile", 
    temperature=0.4, # Higher temperature for copywriting creativity
    api_key=os.getenv("GROQ_API_KEY")
)

structured_llm = llm.with_structured_output(GeneratedCopy)

def creative_node(state: CampaignState) -> dict:
    print("🤖 Agent: Generating email HTML content...")
    
    completed_variants = []
    parsed_brief = state.get("parsed_brief")
    product_details = f"{parsed_brief.product_name}: {parsed_brief.base_return_advantage}." if parsed_brief else ""
    cta_url = parsed_brief.cta_url if parsed_brief else "https://superbfsi.com/xdeposit/explore/"
    
    # Build segment lookup for segment-specific context in the creative prompt
    segments_by_id = {seg.segment_id: seg for seg in state.get("active_segments", [])}
    
    # Build offer-to-segment relevance mapping
    # This ensures each segment's email only mentions offers relevant to THAT segment
    all_offers = parsed_brief.special_offers if parsed_brief else []
    
    def _get_relevant_offers(segment_id: str) -> str:
        """Filter special offers to only those relevant to the target segment."""
        relevant = []
        for offer in all_offers:
            offer_lower = offer.lower()
            # Senior offers → only for senior segments
            if any(kw in offer_lower for kw in ["senior", "60+", "80ttb"]):
                if "senior" in segment_id:
                    relevant.append(offer)
            # Youth offers → only for young adults
            elif any(kw in offer_lower for kw in ["under 25", "first-time", "young", "18-24", "welcome bonus"]):
                if "young" in segment_id:
                    relevant.append(offer)
            # High income offers → high income segment
            elif any(kw in offer_lower for kw in ["premium", "wealth", "high net worth", "hni"]):
                if "high_income" in segment_id:
                    relevant.append(offer)
            else:
                # General offers apply to all segments
                relevant.append(offer)
        return "; ".join(relevant) if relevant else "Standard product offering"
    
    # Check if this is a regeneration run with human feedback
    feedback = state.get("hitl_feedback")
    feedback_instruction = ""
    if feedback and state.get("hitl_status") == "rejected":
        feedback_instruction = f"\n        CRITICAL HUMAN FEEDBACK FOR REGENERATION (OVERRIDE PREVIOUS RULES IF CONFLICTING):\n        \"{feedback}\""
    
    for variant in state.get("current_variants", []):
        # Get segment-specific context
        segment = segments_by_id.get(variant.segment_id)
        segment_context = ""
        if segment:
            segment_context = f"""
        TARGET SEGMENT CONTEXT (tailor content specifically to this audience):
        - Segment: {segment.name}
        - Key Strategy: {segment.strategy_notes}
        - Psychological Hook: {segment.psychological_hook}
        - ONLY mention offers relevant to this segment. Do NOT include offers
          meant for other age groups or demographics."""
        
        relevant_offers = _get_relevant_offers(variant.segment_id)
        
        # --- SEGMENT-SPECIFIC FORMAT RULES ---
        # The gamified API penalizes content that doesn't match demographic expectations.
        # Seniors need plain/simple emails; young adults need CTA-first emails.
        segment_format_rules = ""
        is_senior = "senior" in variant.segment_id.lower()
        is_young = "young" in variant.segment_id.lower()
        
        if is_senior:
            segment_format_rules = """
        SENIOR CITIZEN EMAIL FORMAT RULES (MANDATORY — API PENALIZES VIOLATIONS):
        - Keep the email UNDER 120 words total. Seniors abandon long emails.
        - Use ONLY simple HTML: <p>, <strong>, <em>. NO tables, NO divs, NO lists.
        - ABSOLUTELY ZERO emojis anywhere in subject or body. Override has_emoji to false.
        - Lead the FIRST sentence with the key benefit: Section 80TTB tax savings
          or DICGC-insured safety or the specific return rate number.
        - Use plain, direct language. NO jargon like "portfolio", "compounding",
          "wealth creation". Say "savings", "safe returns", "tax benefit" instead.
        - Include the CTA URL TWICE: once in the middle of the email AND once
          at the very end. Senior readers often miss a single link.
        - Subject line must include one of: "Section 80TTB" or "Senior Citizen"
          or the return rate percentage. Keep subject under 8 words.
        - Address the reader respectfully. Use "Dear Sir/Madam" or "Respected".
        - End with a reassurance line about safety/DICGC insurance.
        """
        elif is_young:
            segment_format_rules = """
        YOUNG ADULT (18-24) EMAIL FORMAT RULES (MANDATORY — BOOSTS CLICK RATE):
        - The CTA URL MUST appear within the FIRST 3 lines of the email body.
          Young adults scroll fast — if the link is at the bottom, they never click.
        - Keep the email UNDER 100 words. Short, punchy, mobile-first.
        - Frame FD as a SMART first financial move, not a conservative one.
          Use phrases like "Your first ₹10,000 grows to...", "Start at 18, retire rich",
          "Beat your savings account by 1%+ — takes 2 minutes".
        - ZERO financial jargon. No "portfolio diversification", "capital preservation",
          "compounding returns". Say "your money grows", "higher interest", "easy start".
        - Use 1-2 relevant emojis maximum (💰, 📈, ✅). No more.
        - Include the CTA URL TWICE: once near the top, once at the end.
        - Subject line should feel peer-driven: "Your friends are earning more on savings"
          or include a specific number like "7.5% returns".
        """
        
        prompt = f"""
        You are an expert email copywriter for SuperBFSI, an Indian BFSI company.
        Write the email subject and HTML body for this specific strategy.

        STRICT CONTENT RULES — VIOLATIONS DISQUALIFY THE SYSTEM:
        1. Email BODY: Only English text, emojis (ONLY if allowed below), and exactly this URL: {cta_url}
        2. Email SUBJECT: Only English text (NO emojis, NO URLs).
        3. NO images, NO attachments, NO external URLs other than the one specified.
        4. BANNED WORDS: Do not use "Free", "FREE", "Guarantee", "Act now", "Limited time", "Click here", "Buy now". Use "guaranteed" or "assured" instead.
        5. Font formatting allowed: <strong>, <em>, <u>. Use them to highlight the requested elements.
        6. Do NOT duplicate text — never write the same phrase both as plain text AND inside a formatting tag like <strong> or <em>.
           WRONG: "Control your finances <strong>Control your finances</strong>"
           CORRECT: "<strong>Control your finances</strong> with our exclusive offer"
        {segment_format_rules}
        {feedback_instruction}
        {segment_context}

        PRODUCT DETAILS:
        {product_details}
        Relevant Special Offers for this segment: {relevant_offers}

        VARIANT STRATEGY INSTRUCTIONS:
        - Tone: {variant.tone}
        - Emojis allowed in body: {"false (ZERO emojis for this segment)" if is_senior else variant.has_emoji} (Positions: {"none" if is_senior else variant.emoji_positions})
        - Phrases to Bold (wrap in <strong> tags): {variant.bold_elements}
        - Phrases to Italicize (wrap in <em> tags): {variant.italic_elements}
        - URL Placement: {"early — within first 3 lines AND at end" if is_young else variant.url_position}
        
        CRITICAL — BOLD & ITALIC USAGE:
        - The bold_elements and italic_elements above are actual phrases to use.
        - Write them NATURALLY inside a sentence, wrapped in the appropriate tag.
        - If any element looks like a placeholder or label (e.g. "CTA", "benefits",
          "headline", "strategy_explanation"), do NOT write it literally.
          Instead, write a real customer-facing phrase that matches that concept.
        - WRONG: "<strong>CTA</strong> and start today" or "<em>strategy_explanation</em>"
        - CORRECT: "<strong>Start your wealth journey today</strong>"

        OUTPUT FORMAT:
        You MUST return the output as a valid JSON object matching this exact structure, with no markdown formatting or extra text:
        {{
            "subject": "Your Subject Line Here",
            "body_html": "<p>Your HTML email body here, with the URL: {cta_url}</p>"
        }}
        """
        
        copy = structured_llm.invoke(prompt)

        # POST-GENERATION VALIDATION
        # Check both subject and body for banned words (case-insensitive)
        combined_text = (copy.subject + " " + copy.body_html).lower()
        violations = [word for word in BANNED_WORDS if word in combined_text]

        if violations:
            print(f"  -> ⚠️  Content violation in {variant.variant_id}: {violations}. Regenerating...")
            stricter_prompt = prompt + f"""

            CRITICAL CORRECTION REQUIRED:
            Your previous response contained these banned words/phrases: {violations}
            These are STRICTLY PROHIBITED in BFSI email marketing.
            Regenerate the email without any of these words.
            Use professional alternatives:
            - Instead of "Limited time" use "Available now"
            - Instead of "Act now" use "Start today"
            - Instead of "Guarantee" use "assured returns" or "DICGC-insured"
            - Instead of "Free" use "complimentary" or remove entirely
            """
            copy = structured_llm.invoke(stricter_prompt)
            print(f"  -> Regenerated {variant.variant_id} after violation correction.")

        # POST-GENERATION: Fix duplicated text around HTML tags
        # Pattern: "phrase <tag>phrase</tag>" → "<tag>phrase</tag>"
        # The LLM sometimes writes plain text and then the same text inside a tag
        body = copy.body_html
        for tag in ["strong", "em", "u"]:
            # Match "text <tag>text</tag>" where the text before the tag matches the text inside
            pattern = rf'(\b[\w\s,.\'-]+?)\s*<{tag}>\1</{tag}>'
            body = re.sub(pattern, rf'<{tag}>\1</{tag}>', body, flags=re.IGNORECASE)
        copy.body_html = body

        # Update the variant with the validated content
        variant.subject = copy.subject
        variant.body_html = copy.body_html
        completed_variants.append(variant)
        
        print(f"  -> Generated Copy for {variant.variant_id}: '{variant.subject}'")
        
    return {"current_variants": completed_variants}