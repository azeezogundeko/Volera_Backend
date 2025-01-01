import asyncio
from typing import Literal

from ..state import State
from utils.logging import logger
from ..followup_agent import FollowUpAgent
from ..config import agent_manager
from .prompts.followup import followup_agent_prompt
from schema import FollowAgentSchema, extract_agent_results
# from utils.exceptions import AgentProcessingError

from fastapi import WebSocket
from langgraph.types import Command
from pydantic_ai.result import RunResult


class InsightsFollowUpAgent(FollowUpAgent):
    def __init__(
        self, 
        result_type = FollowAgentSchema,
        system_prompt = followup_agent_prompt, 
    
    ):
        super().__init__(
            system_prompt=system_prompt,
            result_type=result_type,
            )

    
    @extract_agent_results(agent_manager.followup)
    async def run(self, state: State, user_input)-> RunResult:
        
        previous_messages = state.get("message_history", [])
        searched_results = state["agent_results"][agent_manager.search_tool]
        searched_results = f"Search results: {searched_results}"
        # Call LLM with timeout to avoid hanging
        response = await asyncio.wait_for(self.llm.run(searched_results, message_history=previous_messages), timeout=10)

        state["message_history"] = previous_messages + response.new_messages()
        logger.info("Follow up agent executed successfully.")
        return response

    
    async def __call__(
        self, 
        state: State, 
        config: dict = {}
        ) -> Command[Literal[agent_manager.web_query_agent, agent_manager.human_node, agent_manager.end]]:
        try:
            user_input = state["human_response"] if "human_response" in state else None
            response = await self.run(state, user_input)
            data: FollowAgentSchema = response.data
            state["previous_node"] = agent_manager.followup
            ws_id: WebSocket = state["ws_id"]
            # print(data)
            if data.action == "__user__":
                state["ai_response"] = data.content
                state["next_node"] = agent_manager.followup
                await self.websocket_manager.stream_final_response(ws_id, state["ai_response"])
                return Command(goto=agent_manager.human_node, update=state)

            elif data.action == "__stop__":
                state["ai_response"] = data.content
                state["next_node"] = agent_manager.end
                await self.websocket_manager.stream_final_response(ws_id, state["ai_response"])
                return Command(goto=agent_manager.end, update=state)
            
            state["ai_response"] = data.content
            state["human_response"] = data.user_query
                
            await self.websocket_manager.stream_final_response(ws_id, state["ai_response"])
            logger.info("Transitioning to web search agent node.")
            return Command(goto=agent_manager.web_query_agent, update=state)

        except Exception as e:
            logger.error("Error encountered in followup agent node processing.", exc_info=True)
            # send a response to notify an error has occurred
            # use an error websocket message type
            return Command(goto=agent_manager.end, update=state)


followup_agent_node = InsightsFollowUpAgent()