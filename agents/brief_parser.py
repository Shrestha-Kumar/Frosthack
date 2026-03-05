import os
from langchain_groq import ChatGroq
from models import ParsedBrief, CampaignState

def brief_parser_node(state: CampaignState) -> dict:
    print("🤖 Agent: Parsing brief...")
    
    # Swapped to Groq Llama 3.3 70B for development stability
    llm = ChatGroq(
        model="llama-3.3-70b-versatile", 
        temperature=0, 
        api_key=os.getenv("GROQ_API_KEY")
    )
    
    structured_llm = llm.with_structured_output(ParsedBrief)

    prompt = f"""
    You are a marketing brief analyst for an Indian BFSI company.
    Extract structured information from the campaign brief.

    CRITICAL RULES:
    1. If the brief says "don't skip inactive customers" or similar — set include_inactive = TRUE
    2. Extract ALL special offers mentioned (e.g., extra % for specific demographics)
    3. The CTA URL must be extracted exactly as written
    4. If optimization targets include "click rate" or "CTR", add "click_rate" to optimization_targets
    5. Return ONLY valid JSON matching the ParsedBrief schema. No explanation text.

    Brief: {state['raw_brief']}
    """
    
    parsed_brief = structured_llm.invoke(prompt)
    print(f"✅ Brief parsed! Include Inactive: {parsed_brief.include_inactive}")
    
    return {"parsed_brief": parsed_brief}