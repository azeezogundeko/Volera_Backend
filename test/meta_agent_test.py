from agents import State, agent_manager, meta_agent_node
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
state = State(
    ws_message=[request],
    agent_results={},
    final_result={},
    chat_limit=10,
    chat_finished=False,
    previous_node="",
    previous_search_queries=[],
    message_history=[]
)

async def test_meta_agent_flow(state):
    result = await meta_agent_node(state)
    print(result.goto)

    # assert result.goto == agent_manager.end

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_meta_agent_flow(state))