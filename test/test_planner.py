from agents import State, planner_agent_node, agent_manager
from schema import WSMessage
request = WSMessage(
    user_id="user_id",
    focus_mode=agent_manager.copilot_mode,
    files=["file1", "file2"],
    message={
        "content": "What is the cheapest laptop?"
    },
    history=[],
    optimization_mode="fast",
    
)
requirements = {
    "product_category": "laptop",
    "product_type": "",
    "purpose": "Python Programming",
    "preferred_brands": ["Lenovo", "hp"],
    "budget": "$1000"

}
state = State(
    ws_message=request,
    agent_results={},
    final_result={},
    chat_limit=10,
    chat_finished=False,
    previous_node="",
    previous_search_queries=[],
    message_history=[],
    requirements=requirements
)

async def test_policy_agent_node(state):
    result = await planner_agent_node(state)
    print(result)

if __name__ == "__main__":
    import asyncio

    asyncio.run(test_policy_agent_node(state))