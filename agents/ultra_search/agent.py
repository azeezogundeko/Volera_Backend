from typing import Literal
from asyncio import wait_for, sleep, Semaphore
from datetime import datetime, timedelta

from ..state import State
from .prompt import system_prompt
from ..config import agent_manager
from ..legacy.base import BaseAgent
from .schema import ResultSchema
from ..legacy.llm import check_credits

from utils.logging import logger
from utils.rerank import ReRanker
from utils.url_shortener import URLShortener
from utils.search import extractor
from utils.decorator import async_retry
from utils._craw4ai import CrawlerManager
from schema import GeminiDependencies, extract_agent_results

from langgraph.types import Command


class DeepSearchAgent(BaseAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(
            model="google-gla:gemini-2.0-flash-exp",
            name=agent_manager.web_query_agent,
            system_prompt=system_prompt,
            result_type=ResultSchema,
            deps_type=GeminiDependencies,
            *args, **kwargs
            )
        # Rate limiting: 3 requests per minute
        self._crawl_semaphore = Semaphore(3)
        self._last_crawl_times = []
        self.rerank = ReRanker()
        self.num_results = 30
        self.generate_id = URLShortener()
        
    

    async def search(self, query: str, num_of_results: int = 20):
        query = query + 'Nigeria'

        return await self.search_tool.search_products(query, num_results=num_of_results)

    #     return {}
            
    @async_retry(retries=2, delay=0.1)
    @extract_agent_results(agent_manager.web_query_agent)
    async def run(self, state: State, user_input: str = None): 
        user_id = state.get("user_id")
        if not user_id:
            raise ValueError("User ID not found in state")
        
        # previous_search_results = state["agent_results"][agent_manager.search_tool]
        model_to_use = state.get('model', 'google-gla:gemini-2.0-flash-exp')
        model_config = self.get_model_config(model_to_use)
        # dependencies = self.update_dependencies(model_to_use)

        previous_messages = state.get("message_history", [])
        if user_input is None:
            user_input = state['ws_message']['message']['content']
           
        # Call LLM with timeout to avoid hanging
        response = await wait_for(
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
        logger.info("Query Agent executed successfully.")
        return response
    

    async def __call__(
        self, 
        state: State, 
        config: dict = {}
    )-> Command[Literal[agent_manager.writer_agent, agent_manager.end]]:
        try:
            user_input = state["human_response"] if "human_response" in state else None
            user_id = state["user_id"]
            has_credits, credits = await check_credits(user_id=user_id, type="amount", amount=100)
            if not has_credits:
                raise ValueError(f'Insuffients Credits, Requires {100} Available Creduts: {credits}')
            response = await self.run(state, user_input)
            data = response.data
            state["previous_node"] = agent_manager.web_query_agent
            
            ws_id = state["ws_id"]
            await self.websocket_manager.send_progress(ws_id, "searching", 0)
            
            try:
                response = await wait_for(
                    self.search(data.reviewed_query), 
                    timeout=self.timeout
                )
                # state["task_id"] = task_id
                await self.websocket_manager.send_progress(ws_id, "searching", len(response))
                crawler = await CrawlerManager.get_crawler()

                logger.info('Starting to crawl')
                # count = 0
                # # final_products = []
                urls= []
                results_markdown = []
                for res in response: 
                    urls.append(res['link'])

                await self.websocket_manager.send_progress(ws_id, "scraping", 0)
                crawl_results = await crawler.arun_many(urls=urls, magic=True, bypass_cache=True)
                await self.websocket_manager.send_progress(ws_id, "scraping", len(crawl_results))

                for result in crawl_results:
                    if not result.success:
                        continue
                    
                    # print(result.markdown)
                    results_markdown.append({
                        "url": result.url,
                        "result": result.markdown
                    })
                print(results_markdown)
                state["agent_results"][agent_manager.search_tool] = results_markdown
                logger.info('Transitioning to Writer Agent Node')
                return Command(goto=agent_manager.writer_agent, update=state)
            except ValueError as e:
                if "Insufficient credits" in str(e):
                    await self.websocket_manager.send_json(
                        ws_id,
                        data={
                            "type": "error",
                            "message": str(e)
                        }
                    )
                return Command(goto=agent_manager.end, update=state)

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


deep_search_agent_node = DeepSearchAgent()
        

    


    