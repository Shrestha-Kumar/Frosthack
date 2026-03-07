import os
from langchain_groq import ChatGroq
from pydantic import BaseModel
from typing import List
from models import CampaignState, OptimizationRecord

class OptimizationDecision(BaseModel):
    insight: str
    action_taken: str
    variants_changed: List[str]
    segments_retargeted: List[str]
    should_continue: bool

llm = ChatGroq(
    model="llama-3.3-70b-versatile", 
    temperature=0.1, 
    api_key=os.getenv("GROQ_API_KEY")
)

structured_llm = llm.with_structured_output(OptimizationDecision)

def analytics_node(state: CampaignState) -> dict:
    print("🤖 Agent: Analyzing results and deciding next steps...")
    
    iteration = state.get("iteration_count", 0)
    reports = state.get("performance_reports", [])
    
    # Strip down the data to fit perfectly in the prompt
    perf_data = [
        {
            "variant_id": r.variant_id,
            "segment_id": r.segment_id,
            "click_rate": round(r.click_rate * 100, 1),
            "open_rate": round(r.open_rate * 100, 1),
            "composite_score": round(r.composite_score, 4)
        }
        for r in reports
    ]
    
    prompt = f"""
    You are a marketing analytics AI for SuperBFSI.
    We just completed Iteration {iteration} of our A/B test.
    
    Evaluation Formula: composite_score = (0.7 * click_rate) + (0.3 * open_rate)
    
    Performance data:
    {perf_data}
    
    Analyze the results:
    1. Identify the winning variants per segment.
    2. Write a brief insight on what likely caused the win.
    3. Determine if we should continue optimizing. Return should_continue = True ONLY IF the highest composite score is below 0.85 AND we have actionable ideas for improvement. Otherwise, return False.
    
    Return the structured OptimizationDecision.
    """
    
    decision = structured_llm.invoke(prompt)
    
    opt_record = OptimizationRecord(
        iteration=iteration,
        insight=decision.insight,
        action_taken=decision.action_taken,
        variants_changed=decision.variants_changed,
        segments_retargeted=decision.segments_retargeted
    )
    
    print(f"  -> 🧠 Agent Insight: {decision.insight}")
    print(f"  -> 🔄 Should Continue Loop: {decision.should_continue}")
    
    return {
        "optimization_history": [opt_record],
        "should_continue_optimization": decision.should_continue,
        "iteration_count": iteration + 1
    }