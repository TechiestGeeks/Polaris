import asyncio
from app.graph.state import AgentState
from app.graph.builder import build_graph

async def run_tests():
    graph = build_graph()
    
    # Test 1: Cross-border sharing (India -> EU)
    state1 = AgentState(
        question="Can I share this Indian customer data with the EU team?",
        employee_context={
            "name": "Arjun Mehta", "role": "Senior", "department": "Engineering", 
            "access_level": "L2-SENIOR", "region": "India"
        },
        history=[],
        classification=None,
        parsed_context=None,
        candidate_policies=[],
        decision=None,
        final_response=None,
        escalation_confirmed=False
    )
    
    result1 = await graph.ainvoke(state1)
    print("--- Test 1: Cross Border ---")
    print(result1["final_response"].decision)
    
run_tests_sync = lambda: asyncio.run(run_tests())
if __name__ == "__main__":
    run_tests_sync()
