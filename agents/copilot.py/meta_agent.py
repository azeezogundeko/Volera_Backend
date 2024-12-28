import asyncio
from typing import Literal

from .state import State
from utils.logging import logger
from .config import agent_manager
from .legacy.base import BaseAgent
from .prompts.followup import meta_agent_prompt
from schema import MetaAgentSchema, extract_agent_results
from schema.dataclass.dependencies import GeminiDependencies
from utils.exceptions import AgentProcessingError

from langgraph.types import Command
from fastapi import WebSocket
from pydantic_ai.result import RunResult


class MetaAgent(BaseAgent):
    def __init__(
        self, 
        model = "gemini-2.0-flash-exp",
        deps_type = GeminiDependencies,
        result_type = MetaAgentSchema,
        system_prompt = meta_agent_prompt,
        name: str = agent_manager.meta_agent, 
    
    ):
        super().__init__(
            name,
            model,
            system_prompt,
            result_type,
            deps_type,
            )

    
    @extract_agent_results(agent_manager.meta_agent)
    async def run(self, state: State)-> RunResult:
    
        previous_messages = state.get("message_history", [])
        user_input = state["human_response"]
        # Call LLM with timeout to avoid hanging
        response = await asyncio.wait_for(self.llm.run(user_input, message_history=previous_messages), timeout=10)

        state["message_history"] = previous_messages + response.new_messages()
        logger.info("Meta agent executed successfully.")
        return response


    async def __call__(
        self, 
        state: State, 
        config: dict = {}
        ) -> Command[Literal[agent_manager.planner_agent]]:
        try:
            response = await self.run(state)
            user_input = state["human_response"] if "human_response" in state else None
            data: MetaAgentSchema = response.data
            state["previous_node"] = agent_manager.meta_agent
            if data.action == "__user__":
                state["ai_response"] = data.content
                state["next_node"] = agent_manager.meta_agent
                return Command(goto=agent_manager.human_node, update=state)
            
            state["requirements"] = data.content
            state["ai_response"] = data.content
            state["requirements"] = data.requirements
                
            ws: WebSocket = state["ws"]
            await ws.send_json({"type": "message","content": state["ai_response"]})
            await ws.send_json({"type": "messageEnd"})
            logger.info("Transitioning to planner agent node.")
            return Command(goto=agent_manager.planner_agent, update=state)

        except Exception as e:
            logger.error("Error encountered in followup agent node processing.", exc_info=True)
            # send a response to notify an error has occurred
            # use an error websocket message type
            return Command(goto=agent_manager.end, update=state)