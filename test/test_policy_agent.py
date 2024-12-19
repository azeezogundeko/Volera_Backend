import pytest
import pytest_asyncio
from agents import State, policy_agent_node, agent_manager
from schema import WSMessage
from unittest.mock import AsyncMock, patch

@pytest_asyncio.fixture
async def base_state():
    request = WSMessage(
        user_id="user_id",
        focus_mode=agent_manager.copilot_mode,
        files=["file1", "file2"],
        message={
            "content": "What is the capital of France?"
        },
        history=[],
        optimization_mode="fast"
    )
    return State(current_request=[request])

@pytest_asyncio.mark.asyncio
async def test_policy_agent_node_copilot_mode(base_state):
    """
    Test policy_agent_node with copilot mode, expecting transition to meta_agent
    """
    with patch('agents.policy.policy_agent') as mock_policy_agent:
        # Simulate a compliant request
        mock_policy_agent.return_value = AsyncMock(
            data=AsyncMock(complaint=True)
        )
        
        result = await policy_agent_node(base_state)
        
        assert result.goto == agent_manager.meta_agent

@pytest_asyncio.mark.asyncio
async def test_policy_agent_node_end_mode(base_state):
    """
    Test policy_agent_node when complaint is False, expecting transition to end
    """
    with patch('agents.policy.policy_agent') as mock_policy_agent:
        # Simulate a non-compliant request
        mock_policy_agent.return_value = AsyncMock(
            data=AsyncMock(complaint=False)
        )
        
        result = await policy_agent_node(base_state)
        
        assert result.goto == agent_manager.end

@pytest_asyncio.mark.asyncio
async def test_policy_agent_node_invalid_request():
    """
    Test policy_agent_node with an invalid request, expecting a ValueError
    """
    invalid_state = State(current_request=[{}])
    
    with pytest.raises(ValueError, match="Invalid or missing 'content' in current request."):
        await policy_agent_node(invalid_state)

@pytest_asyncio.mark.asyncio
async def test_policy_agent_node_search_mode():
    """
    Test policy_agent_node with search mode, expecting transition to search_agent
    """
    request = WSMessage(
        user_id="user_id",
        focus_mode=agent_manager.normal_mode,  # Not copilot mode
        files=["file1", "file2"],
        message={
            "content": "Search for laptops"
        },
        history=[],
        optimization_mode="fast"
    )
    state = State(current_request=[request])
    
    with patch('agents.policy.policy_agent') as mock_policy_agent:
        # Simulate a compliant request
        mock_policy_agent.return_value = AsyncMock(
            data=AsyncMock(complaint=True)
        )
        
        result = await policy_agent_node(state)
        
        assert result.goto == agent_manager.search_agent