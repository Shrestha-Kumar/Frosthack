import asyncio
from graph import build_campaign_graph

async def test_run():
    print("🚀 Starting Graph Test...")
    graph = build_campaign_graph()
    
    # We need a thread_id so the MemorySaver knows where to store the state
    config = {"configurable": {"thread_id": "test_campaign_001"}}
    
    # 1. Run until the interrupt
    print("\n--- Phase 1: Running Initial Graph ---")
    async for event in graph.astream({"raw_brief": "Test brief", "max_iterations": 3, "should_continue_optimization": False}, config=config):
        print(f"Executed node: {list(event.keys())[0]}")
        
    # Check where we paused
    current_state = graph.get_state(config)
    print("\n⏸️ Graph Paused!")
    print(f"Next node to execute: {current_state.next}")
    
    if current_state.next == ("hitl_approval",):
        print("\n--- Phase 2: Simulating Human Approval ---")
        # Update the state to simulate the human clicking "Approve"
        graph.update_state(config, {"hitl_status": "approved"})
        
        # Resume the graph
        print("▶️ Resuming Graph...")
        async for event in graph.astream(None, config=config):
            print(f"Executed node: {list(event.keys())[0]}")
            
    print("\n🏁 Graph Test Complete!")

if __name__ == "__main__":
    asyncio.run(test_run())