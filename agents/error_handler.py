import os
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field

# The structured output we want from the LLM
class ErrorFix(BaseModel):
    insight: str = Field(description="Explanation of why the API call failed.")
    action: str = Field(description="The action to take: 'retry', 'fix_payload', or 'skip'.")

def error_correction_node(state: dict) -> dict:
    print("⚠️ Agent: Self-healing triggered. Analyzing error...")
    
    # Get the latest error
    error_log = state.get("api_error_log", [])
    if not error_log:
        return {"api_error_log": []}
        
    last_error = error_log[-1]
    
    llm = ChatGroq(
        model="llama-3.3-70b-versatile", 
        api_key=os.getenv("GROQ_API_KEY")
    )
    structured_llm = llm.with_structured_output(ErrorFix)
    
    prompt = f"""
    You are a System Reliability Agent for an autonomous marketing system.
    The Execution Agent just tried to call an API and received this error:
    
    {last_error}
    
    Analyze this error. 
    1. If it's a Rate Limit (429), we should just 'retry'.
    2. If it's a Validation Error (422), we need to 'fix_payload'.
    3. If the server is dead (500), we should 'skip' to avoid infinite loops.
    
    Determine the best action.
    """
    
    try:
        fix = structured_llm.invoke(prompt)
        print(f"  -> Recovery Strategy: {fix.action} ({fix.insight})")
    except Exception as e:
        print(f"  -> Recovery Strategy failed: {e}. Defaulting to skip.")
        
    # We clear the error log so the execution node can try fresh, 
    # but we could also pass a "correction_instruction" back to the state if we wanted to get fancy.
    return {
        "api_error_log": [] # Clear the error to prevent infinite loops
    }