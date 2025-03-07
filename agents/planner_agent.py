import asyncio
from typing import Literal

from utils.logging import logger
from .config import agent_manager
from .state import State
from .legacy.base import BaseAgent
from prompts import planner_agent_prompt
from schema import PlannerAgentSchema, extract_agent_results
from .tools.search_tool import search_internet_tool
from schema.dataclass.dependencies import GeminiDependencies
from utils.exceptions import AgentProcessingError, NoItemFound

from langgraph.types import Command
from pydantic_ai.result import ResultDataT


class PlannerAgent(BaseAgent):
    def __init__(
        self, 
        timeout=10,
        model = "gemini-2.0-flash-exp",
        deps_type = GeminiDependencies,
        result_type = PlannerAgentSchema,
        system_prompt = planner_agent_prompt,
        name: str = agent_manager.planner_agent, 
    
    ):
        super().__init__(
            name=name,
            retries=3,
            model=model,
            timeout=timeout,
            deps_type=deps_type,
            result_type=result_type,
            system_prompt=system_prompt,
        )

    @extract_agent_results(agent_manager.planner_agent)
    async def run(self, state: State, config: dict = {}) -> ResultDataT:
        try:
            user_query = state["ws_message"]["message"]["content"]
            past_conversations = state["message_history"]
            response = await asyncio.wait_for(
                self.llm.run(user_query, message_history=past_conversations), 
                timeout=self.timeout
                )
            logger.info("Planner agent executed successfully.")
            return response
        except Exception as e:
            logger.error("Unexpected error in Planner agent execution.", exc_info=True)
            raise AgentProcessingError(f"Unexpected error during planner agent execution.{str(e)}")

    async def search(self, result: PlannerAgentSchema):
        return await search_internet_tool(
            search_query=result.product_retriever_query,
            description=result.description,
            filter=result.filter,
            n_k=result.n_k,
            mode="fast",
            type="ecommerce"
        )

    async def __call__(self, state: State, config: dict = {}) -> Command[Literal[agent_manager.writer_agent]]:
        try: 
            ws_id = state["ws_id"]
            result = await self.run(state)

            # started searching the internet
            await self.websocket_manager.send_progress(ws_id, "searching", 0)
            response = await self.search(result.data)
            
            await self.websocket_manager.send_progress(ws_id, "searching", len(response))
        

        except NoItemFound as e:
            state["ai_response"] = self.get_random_message()
            state["next_node"] = agent_manager.meta_agent
            state["previous_node"] = agent_manager.planner_agent
            return Command(goto=agent_manager.human_node, update=state)

        state["agent_results"][agent_manager.search_tool] = response
        logger.info("Transitioning to writer agent node.")
        return Command(goto=agent_manager.writer_agent, update=state)


    def get_random_message(self) -> str:
        messages = [
            "Sorry, I could not find any relevant products.",
            "Unfortunately, no relevant products were found.",
            "I wasn't able to locate any suitable products.",
            "Regrettably, I couldn't find any matching products.",
            "No relevant products were found at this time.",
            "I'm sorry, but there are no products that match your query.",
            "It seems there are no products available that fit your needs.",
            "Apologies, but I couldn't find any products that match.",
            "I couldn't locate any relevant items.",
            "Sadly, there are no products to display.",
            "I wasn't able to find any products that meet your criteria.",
            "Unfortunately, I couldn't find any items that match your request.",
            "No products were found that fit your search.",
            "Sorry, but I couldn't find any items related to your query.",
            "There are no relevant products available at the moment.",
            "I couldn't find any suitable items for you.",
            "Unfortunately, no products match your search criteria.",
            "I'm sorry, but I couldn't find any relevant items.",
            "It appears there are no products available that meet your needs.",
            "Regrettably, I couldn't locate any matching items.",
            "I wasn't able to find any relevant products at this time."
        ]
        import random
        return random.choice(messages)


planner_agent_node = PlannerAgent()