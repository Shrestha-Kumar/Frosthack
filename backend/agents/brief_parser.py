import os
import itertools as _itertools
from langchain_groq import ChatGroq
from models import ParsedBrief, CampaignState

# Brief parser needs 70B for reliable structured output with List[str] fields.
# Called only ONCE per run (~700 tokens) — negligible rate-limit impact.
BRIEF_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

def _build_key_cycle():
    keys = [k for k in [
        os.getenv("GROQ_API_KEY"),
        os.getenv("GROQ_API_KEY_2"),
        os.getenv("GROQ_API_KEY_3"),
        os.getenv("GROQ_API_KEY_4"),
        os.getenv("GROQ_API_KEY_5"),
    ] if k]
    if not keys:
        raise ValueError("No GROQ API keys found in environment!")
    print(f"  🔑 [brief_parser] Groq key rotation: {len(keys)} key(s) loaded")
    return _itertools.cycle(keys)

_key_cycle = _build_key_cycle()

def _get_llm():
    return ChatGroq(model=BRIEF_MODEL, temperature=0, api_key=next(_key_cycle))

structured_llm = _get_llm().with_structured_output(ParsedBrief)

def brief_parser_node(state: CampaignState) -> dict:
    print("🤖 Agent: Parsing brief...")
    structured_llm = _get_llm().with_structured_output(ParsedBrief)

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