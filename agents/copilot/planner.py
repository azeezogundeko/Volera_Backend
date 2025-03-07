import asyncio

from ..planner_agent import PlannerAgent
from ..config import agent_manager
from pydantic_ai.result import ResultDataT
from ..state import State
from utils.logging import logger
from schema import extract_agent_results
from utils.exceptions import AgentProcessingError


class CopilotPlannerAgent(PlannerAgent):

    @extract_agent_results(agent_manager.planner_agent)
    async def run(self, state: State, config: dict = {}) -> ResultDataT:
        try:
            requirements = state["requirements"]
            past_conversations = state["message_history"]
            response = await asyncio.wait_for(
                self.llm.run(str(requirements), message_history=past_conversations), 
                timeout=self.timeout
                )
            logger.info(f"{agent_manager.planner_agent} executed successfully.")
            return response
        except Exception as e:
            logger.error(f"Unexpected error in {agent_manager.planner_agent} execution.", exc_info=True)
            raise AgentProcessingError(f"Unexpected error during {agent_manager.planner_agent} execution.{str(e)}")

planner_agent_node = CopilotPlannerAgent()