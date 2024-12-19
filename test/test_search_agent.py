from agents import State, agent_manager, search_agent_node
from schema import WSMessage
# 'Find the cheapest laptop available on the market.  Consider all major retailers and brands.', 'Provide the name of the laptop, its price, and where it can be purchased.', 'If multiple laptops share the same lowest price, list them all. '
request = WSMessage(
    user_id="user_id",
    focus_mode=agent_manager.copilot_mode,
    files=["file1", "file2"],
    message={
        "content": "What is the cheapest Lenovo laptop?"
    },
    history=[],
    optimization_mode="fast",
    
)
state = State(
    ws_message=[request],
    agent_results={
        agent_manager.meta_agent: {
            "next_node": agent_manager.comparison_agent,
            "instructions": "Find the cheapest laptop available on the market.  Consider all major retailers and brands."
        }
    },
    final_result={},
    chat_limit=10,
    chat_finished=False,
    previous_node="",
    previous_search_queries=[],
    message_history=[]
)


async def test_search_agent_node():
    result = await search_agent_node(state)


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_search_agent_node())

