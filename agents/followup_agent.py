import asyncio
from typing import Literal

from .state import State
from utils.logging import logger
from .config import agent_manager
from .legacy.base import BaseAgent
from prompts import followup_agent_prompt
from schema import MetaAgentSchema, extract_agent_results
from schema.dataclass.dependencies import GeminiDependencies
# from utils.exceptions import AgentProcessingError

from fastapi import WebSocket
from langgraph.types import Command
from pydantic_ai.result import RunResult


class FollowUpAgent(BaseAgent):
    def __init__(
        self, 
        model = "gemini-2.0-flash-exp",
        deps_type = GeminiDependencies,
        result_type = MetaAgentSchema,
        system_prompt = followup_agent_prompt,
        name: str = agent_manager.followup, 
    
    ):
        super().__init__(
            name=name,
            model=model,
            system_prompt=system_prompt,
            result_type=result_type,
            deps_type=deps_type
            )

    
    @extract_agent_results(agent_manager.followup)
    async def run(self, state: State, user_input)-> RunResult:
        
        previous_messages = state.get("message_history", [])
        searched_results = state["agent_results"][agent_manager.search_tool]
        searched_results = f"Search results: {searched_results}"
        # Call LLM with timeout to avoid hanging
        response = await asyncio.wait_for(self.llm.run(searched_results, message_history=previous_messages), timeout=10)

        state["message_history"] = previous_messages + response.new_messages()
        logger.info("Meta agent executed successfully.")
        return response

    
    async def __call__(
        self, 
        state: State, 
        config: dict = {}
        ) -> Command[Literal[agent_manager.planner_agent, agent_manager.human_node, agent_manager.end]]:
        try:
            user_input = state["human_response"] if "human_response" in state else None
            response = await self.run(state, user_input)
            data: MetaAgentSchema = response.data
            state["previous_node"] = agent_manager.meta_agent
            # print(data)
            if data.action == "__user__":
                state["ai_response"] = data.content
                state["next_node"] = agent_manager.meta_agent
                return Command(goto=agent_manager.human_node, update=state)

            elif data.action == "__stop__":
                state["ai_response"] = data.content
                state["next_node"] = agent_manager.end
                await self.websocket_manager.stream_final_response(ws_id, state["ai_response"])
                return Command(goto=agent_manager.end, update=state)
            
            state["requirements"] = data.content
            state["ai_response"] = data.content
            state["requirements"] = data.requirements
                
            ws_id: WebSocket = state["ws_id"]
            await self.websocket_manager.stream_final_response(ws_id, state["ai_response"])
            logger.info("Transitioning to planner agent node.")
            return Command(goto=agent_manager.planner_agent, update=state)

        except Exception as e:
            logger.error("Error encountered in followup agent node processing.", exc_info=True)
            # send a response to notify an error has occurred
            # use an error websocket message type
            return Command(goto=agent_manager.end, update=state)


followup_agent_node = FollowUpAgent()