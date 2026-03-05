import os
from langchain_groq import ChatGroq
from pydantic import BaseModel
from models import CampaignState, EmailVariant

class GeneratedCopy(BaseModel):
    subject: str
    body_html: str

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
        
        # Update the variant with the generated content
        variant.subject = copy.subject
        variant.body_html = copy.body_html
        completed_variants.append(variant)
        
        print(f"  -> Generated Copy for {variant.variant_id}: '{variant.subject}'")
        
    return {"current_variants": completed_variants}