import asyncio
from typing import Literal

# from fastapi import WebSocket, WebSocketDisconnect

from ..legacy.base import BaseAgent
from ..tools.search import search_tool
from ..config import agent_manager
from ..state import State
from .prompts.web_prompts import web_query_retrieval_prompt
from .schema import WebQueryAgentSchema
from utils.decorator import async_retry
from utils.logging import logger
from schema import extract_agent_results, GeminiDependencies

from langgraph.store.base import BaseStore
# from ..legacy.llm import check_credits, track_llm_call

# from .prompts.planner_prompts import 

from langgraph.types import Command


class WebQueryAgent(BaseAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(
            model="google-gla:gemini-2.0-flash-exp",
            name=agent_manager.web_query_agent,
            system_prompt=web_query_retrieval_prompt,
            result_type=WebQueryAgentSchema,
            deps_type=GeminiDependencies,
            *args, **kwargs
            )
        
        self.search_tool = search_tool
    
    async def search(self, result: WebQueryAgentSchema, query: str, user_id: str):

        # params = {
        #     "user_id": user_id,
        #     "query": query,
        #     "site": "all",
        #     "max_results": 3,
        #     "limit": 5           
        #     }
        # task_id = await self.background_task.add_task(self.list_product, **params)
        tasks = [
            self.search_tool.search(query=result.search_query),
            self.search_tool.search_images(query=result.search_query),
        ]

        tasks = await asyncio.gather(*tasks)
        results = {
            "search": tasks[0],
            "image": tasks[1],
        }

        # Track credit usage for search operation
        # await track_llm_call(user_id, "text", {"input_tokens": 0, "output_tokens": 0, "total_tokens": 5})
        return results

    @async_retry(retries=2, delay=0.1)
    @extract_agent_results(agent_manager.web_query_agent)
    async def run(self, state: State, user_input: str, store: BaseStore): 
        user_id = state.get("user_id")
        if not user_id:
            raise ValueError("User ID not found in state")

        previous_messages = state.get("message_history", [])
        if user_input is None:
            user_input = state['ws_message']['data']['content']

        model_config = self.get_model_config(state["model"])
        memories = store.search(state["namespace"], query=user_input, limit=3)

        user_prompt = {
            "USER Query": user_input,
            "PAST CONVERSATION SUMMARIES": memories
        }

        # print(user_prompt)
            
        # Call LLM with timeout to avoid hanging
        response = await asyncio.wait_for(
            self.call_llm(
                user_id=user_id,
                user_prompt=str(user_prompt),
                type='text',
                message_history=previous_messages,
                deps=model_config['deps'],
                model=model_config["model"]
                ),
            timeout=120
            )
        
        print(response.data)

        state["message_history"] = previous_messages + response.new_messages()
        logger.info("Web Query Agent executed successfully.")
        return response

    async def __call__(
        self, 
        state: State, 
        config: dict = {},
        *,
        store: BaseStore
    )-> Command[Literal[agent_manager.human_node, agent_manager.writer_agent, agent_manager.end]]:
        try:
            user_input = state["human_response"] if "human_response" in state else None
            response = await self.run(state, user_input, store)
            user_id = state["user_id"]
            data: WebQueryAgentSchema = response.data
            state["previous_node"] = agent_manager.web_query_agent

            if "user" in data.action:
                return await self.go_to_user_node(
                    state, ai_response=data.content, go_back_to_node=agent_manager.web_query_agent
                )
            
            ws_id = state["ws_id"]
            await self.websocket_manager.send_progress(ws_id, "searching", 0)
            
            response = await asyncio.wait_for(
                self.search(response.data, data.search_query, user_id), 
                timeout=self.timeout
            )
            await self.websocket_manager.send_progress(ws_id, "searching", len(response["search"]))
            state["agent_results"][agent_manager.search_tool] = response
            logger.info("Transitioning to Writer agent node.")
            return Command(goto=agent_manager.writer_agent, update=state)
           

        except Exception as e:
            logger.error("Error encountered in followup agent node processing.", exc_info=True)
            await self.websocket_manager.send_json(
                state["ws_id"],
                data={
                    "type": "error",
                    "message": "An error occurred while processing your request."
                }
            )
            return Command(goto=agent_manager.end, update=state)

    


web_query_agent_node = WebQueryAgent()