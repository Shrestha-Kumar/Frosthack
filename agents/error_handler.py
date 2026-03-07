import os
from langchain_groq import ChatGroq
from pydantic import BaseModel
from models import CampaignState

class ErrorFix(BaseModel):
    action: str
    insight: str

# FIX 7: Module-level LLM instantiation
llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=os.getenv("GROQ_API_KEY"))
structured_llm = llm.with_structured_output(ErrorFix)

def error_correction_node(state: CampaignState) -> dict:
    print("⚠️ Agent: Self-healing triggered. Analyzing error...")
    errors = state.get("api_error_log", [])
    
    prompt = f"""
    You are an API error recovery agent.
    The previous execution failed with these errors: {errors}
    Decide whether to 'retry', 'fix_payload', or 'skip'.
    """
    
    # FIX 2: Proper routing logic based on LLM decision
    try:
        fix = structured_llm.invoke(prompt)
        print(f"  -> Recovery Strategy: {fix.action} ({fix.insight})")
        
        if fix.action == "skip":
            return {"api_error_log": ["SKIP"]}
        else:
            return {"api_error_log": []}
            
    except Exception as e:
        print(f"  -> Recovery failed: {e}. Defaulting to skip.")
        return {"api_error_log": ["SKIP"]}