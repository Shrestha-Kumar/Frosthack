import asyncio
from graph import build_campaign_graph

async def run_agent_test():
    print("🚀 Starting Agent Pipeline Test...")
    graph = build_campaign_graph()
    config = {"configurable": {"thread_id": "agent_test_001"}}
    
    # The exact brief from the rulebook to test the 'inactive' trap
    test_brief = "Run email campaign for launching XDeposit, a flagship term deposit product from SuperBFSI, that gives 1 percentage point higher returns than its competitors. Announce an additional 0.25 percentage point higher returns for female senior citizens. Optimise for open rate and click rate. Don't skip emails to customers marked 'inactive'. Include the call to action: https://superbfsi.com/xdeposit/explore/."
    
    print("\n--- Running Graph ---")
    
    # Run the graph. It will execute the real nodes, then the dummy nodes, and pause at the HITL interrupt.
    async for event in graph.astream(
        {"raw_brief": test_brief, "max_iterations": 3, "should_continue_optimization": False}, 
        config=config
    ):
        node_name = list(event.keys())[0]
        print(f"\n✅ Executed node: {node_name}")
        
        # Print the specific outputs from our new nodes
        if node_name == "parse_brief":
            parsed = event[node_name]['parsed_brief']
            print(f"   -> Parsed Product: {parsed.product_name}")
            print(f"   -> Include Inactive Customers: {parsed.include_inactive}")
            
        elif node_name == "profile_customers":
            cohort = event[node_name]['full_cohort']
            segments = event[node_name]['active_segments']
            print(f"   -> Total Cohort Fetched: {len(cohort)}")
            print(f"   -> Segments Created: {[s.name for s in segments]}")

    print("\n🏁 Agent Test Complete! Graph successfully hit the HITL interrupt.")

if __name__ == "__main__":
    asyncio.run(run_agent_test())