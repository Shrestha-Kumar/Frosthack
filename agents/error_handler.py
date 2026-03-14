import os
import itertools as _itertools
from langchain_groq import ChatGroq
from pydantic import BaseModel
from models import CampaignState

class ErrorFix(BaseModel):
    action: str   # "retry", "fix_payload", or "skip"
    insight: str

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

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
    return _itertools.cycle(keys)

_key_cycle = _build_key_cycle()

def _get_llm():
    return ChatGroq(model=GROQ_MODEL, api_key=next(_key_cycle))

MAX_RETRIES = 3

def error_correction_node(state: CampaignState) -> dict:
    print("⚠️ Agent: Self-healing triggered. Analyzing error...")
    errors = state.get("api_error_log", [])
    retry_count = state.get("api_retry_count", 0)

    # Hard cap on retries regardless of LLM decision
    # Prevents infinite loop if API is consistently down
    if retry_count >= MAX_RETRIES:
        print(f"  -> Max retries ({MAX_RETRIES}) reached. Force skipping to metrics.")
        return {
            "api_error_log": ["SKIP"],
            "api_retry_count": 0  # Reset for potential next iteration
        }

    prompt = f"""
    You are an API error recovery agent.
    The previous execution failed with these errors: {errors}
    This is retry attempt {retry_count + 1} of {MAX_RETRIES}.
    Decide whether to 'retry', 'fix_payload', or 'skip'.
    If this is attempt 2 or higher and errors are the same, prefer 'skip'.
    """
    
    try:
        structured_llm = _get_llm().with_structured_output(ErrorFix)
        fix = structured_llm.invoke(prompt)
        print(f"  -> Recovery Strategy: {fix.action} ({fix.insight})")
        
        if fix.action == "skip":
            return {
                "api_error_log": ["SKIP"],
                "api_retry_count": 0
            }
        else:
            # Retry: increment counter, clear error log
            return {
                "api_error_log": [],
                "api_retry_count": retry_count + 1
            }
            
    except Exception as e:
        print(f"  -> Recovery LLM failed: {e}. Defaulting to skip.")
        return {
            "api_error_log": ["SKIP"],
            "api_retry_count": 0
        }