import asyncio
from typing import Literal

from ..legacy.base import BaseAgent
from ..planner_agent import PlannerAgent
from .prompt import planner_system_prompt
from ..config import agent_manager
from ..state import State
from .schema import PlannerSchema
from schema import extract_agent_results

from utils.logging import logger

from pydantic_ai.result import ResultDataT
from langgraph.types import Command


class PlannerAgent(BaseAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(
            name=agent_manager.planner_agent,
            model='google-gla:gemini-2.0-flash-exp', 
            system_prompt=planner_system_prompt, 
            result_type=PlannerSchema, **kwargs)


    @extract_agent_results(agent_manager.planner_agent)
    async def run(self, state: State, config: dict = {}) -> ResultDataT:
        user_input = state["human_response"] if "human_response" in state else None
        if user_input is None:
            user_input = state['ws_message']['message']['content']

        user_id = state['user_id']
        previous_messages = state.get("message_history", [])

        model_to_use = state['model']
        model_config = self.get_model_config(model_to_use)

        response = await asyncio.wait_for(
            self.call_llm(
                user_id=user_id,
                user_prompt=user_input,
                type='text',
                message_history=previous_messages,
                model=model_config['model'],
                deps=model_config['deps']
                ),
            timeout=20
            )
        state["message_history"] = previous_messages + response.new_messages()
        logger.info("Planner agent executed successfully.")
        return response
    
    async def __call__(self, state: State, config: dict = {})-> Command[
        Literal[agent_manager.research_agent, agent_manager.human_node]]:

        response = await self.run(state, config)
        data = response.data

        if data.action == '__user__':

            await self.go_to_user_node(state, data.content, agent_manager.planner_agent)
            logger.info("Routing to Human Node")
            return Command(goto=agent_manager.human_node, update=state)
        try:
            await self.websocket_manager.send_progress(state['ws_id'], status="comment", comment=data.comment)
        except Exception as e:
            logger.error(e, exc_info=True)
        logger.info("Routing to Research Agent")
        return Command(goto=agent_manager.research_agent, update=state)
        

planner_agent = PlannerAgent()