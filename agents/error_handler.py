import os
from langchain_groq import ChatGroq
from pydantic import BaseModel
from models import CampaignState

class ErrorFix(BaseModel):
    action: str   # "retry", "fix_payload", or "skip"
    insight: str

llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=os.getenv("GROQ_API_KEY"))
structured_llm = llm.with_structured_output(ErrorFix)

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