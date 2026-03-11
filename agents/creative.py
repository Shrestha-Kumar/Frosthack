import os
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
    product_details = f"{parsed_brief.product_name}: {parsed_brief.base_return_advantage}. Special: {parsed_brief.special_offers}" if parsed_brief else ""
    cta_url = parsed_brief.cta_url if parsed_brief else "https://superbfsi.com/xdeposit/explore/"
    
    # Check if this is a regeneration run with human feedback
    feedback = state.get("hitl_feedback")
    feedback_instruction = ""
    if feedback and state.get("hitl_status") == "rejected":
        feedback_instruction = f"\n        CRITICAL HUMAN FEEDBACK FOR REGENERATION (OVERRIDE PREVIOUS RULES IF CONFLICTING):\n        \"{feedback}\""
    
    for variant in state.get("current_variants", []):
        prompt = f"""
        You are an expert email copywriter for SuperBFSI, an Indian BFSI company.
        Write the email subject and HTML body for this specific strategy.

        STRICT CONTENT RULES — VIOLATIONS DISQUALIFY THE SYSTEM:
        1. Email BODY: Only English text, emojis, and exactly this URL: {cta_url}
        2. Email SUBJECT: Only English text (NO emojis, NO URLs).
        3. NO images, NO attachments, NO external URLs other than the one specified.
        4. BANNED WORDS: Do not use "Free", "FREE", "Guarantee", "Act now", "Limited time", "Click here", "Buy now". Use "guaranteed" or "assured" instead.
        5. Font formatting allowed: <strong>, <em>, <u>. Use them to highlight the requested elements.
        {feedback_instruction}

        PRODUCT DETAILS:
        {product_details}

        VARIANT STRATEGY INSTRUCTIONS:
        - Tone: {variant.tone}
        - Emojis allowed in body: {variant.has_emoji} (Positions: {variant.emoji_positions})
        - Elements to Bold: {variant.bold_elements}
        - Elements to Italicize: {variant.italic_elements}
        - URL Placement: {variant.url_position}

        OUTPUT FORMAT:
        You MUST return the output as a valid JSON object matching this exact structure, with no markdown formatting or extra text:
        {{
            "subject": "Your Subject Line Here",
            "body_html": "<p>Your HTML email body here, ending with the URL: {cta_url}</p>"
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

        # Update the variant with the validated content
        variant.subject = copy.subject
        variant.body_html = copy.body_html
        completed_variants.append(variant)
        
        print(f"  -> Generated Copy for {variant.variant_id}: '{variant.subject}'")
        
    return {"current_variants": completed_variants}