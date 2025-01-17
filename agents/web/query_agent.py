import asyncio
from typing import Literal

from fastapi import WebSocket

from ..legacy.base import BaseAgent
from ..tools.google import GoogleSearchTool
from ..config import agent_manager
from ..state import State
from .prompts.web_prompts import web_query_retrieval_prompt
from .schema import WebQueryAgentSchema
from utils.decorator import async_retry
from utils.logging import logger
from schema import extract_agent_results, GeminiDependencies

# from .prompts.planner_prompts import 

from langgraph.types import Command


class WebQueryAgent(BaseAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(
            model="gemini-2.0-flash-exp",
            name=agent_manager.web_query_agent,
            system_prompt=web_query_retrieval_prompt,
            result_type=WebQueryAgentSchema,
            deps_type=GeminiDependencies,
            *args, **kwargs
            )
        
        self.search_tool = GoogleSearchTool()
    
    async def search(self, result: WebQueryAgentSchema, ws: WebSocket, query: str):
        params = {
            "query": query,
            "site": "all",
            "max_results": 3,
            "limit": 5           
            }
        task_id = await self.background_task.add_task(self.list_product, **params)
        tasks = [
            self.search_tool.search(query=result.search_query),
            self.search_tool.search_images(query=result.search_query),
        ]


        tasks = await asyncio.gather(*tasks)
        results = {
            "search": tasks[0],
            "image": tasks[1],
        }
        return results, task_id

    @async_retry(retries=2, delay=0.1)
    @extract_agent_results(agent_manager.web_query_agent)
    async def run(self, state: State, user_input: str = None): 
        previous_messages = state.get("message_history", [])
        if user_input is None:
            user_input= state['ws_message']['message']['content']
        # Call LLM with timeout to avoid hanging
        response = await asyncio.wait_for(
            self.llm.run(user_input, message_history=previous_messages),
             timeout=20)

        state["message_history"] = previous_messages + response.new_messages()
        logger.info("Web Query Agent executed successfully.")
        return response

    async def __call__(
        self, 
        state: State, 
        config: dict = {}
    )-> Command[Literal[agent_manager.human_node, agent_manager.writer_agent, agent_manager.end]]:
        try:
            user_input = state["human_response"] if "human_response" in state else None
            response = await self.run(state, user_input)
            data: WebQueryAgentSchema = response.data
            state["previous_node"] = agent_manager.web_query_agent
            # print(data)
            if data.action == "__user__":
                state["ai_response"] = data.content
                await self.websocket_manager.stream_final_response(state["ws_id"], state["ai_response"])
                state["next_node"] = agent_manager.web_query_agent
                return Command(goto=agent_manager.human_node, update=state)
            
            ws_id = state["ws_id"]
            ws = self.websocket_manager.get_websocket(ws_id)
            await self.websocket_manager.send_progress(ws_id, "searching", 0)
            response, task_id = await asyncio.wait_for(self.search(response.data, ws, data.search_query), timeout=self.timeout)

            state["task_id"] = task_id
            await self.websocket_manager.send_progress(ws_id, "searching", len(response["search"]))

            state["agent_results"][agent_manager.search_tool] = response
            logger.info("Transitioning to Writer agent node.")
            return Command(goto=agent_manager.writer_agent, update=state)

        except Exception as e:
            logger.error("Error encountered in followup agent node processing.", exc_info=True)
            # send a response to notify an error has occurred
            # use an error websocket message type
            return Command(goto=agent_manager.end, update=state)


web_query_agent_node = WebQueryAgent()