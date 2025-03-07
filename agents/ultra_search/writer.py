from asyncio import sleep

from ..writer import WriterAgent
from .schema import Product

from typing import Literal

from ..state import State
from ..config import agent_manager
# from ..legacy.llm import check_credits, track_llm_call
from .prompt import product_extractor_prompt

from langgraph.types import Command
from utils.logging import logger
from utils.rerank import ReRanker
from utils.url_shortener import URLShortener

rerank = ReRanker()
url_shortener = URLShortener()


class UltraWriterAgent(WriterAgent):
    def __init__(self, system_prompt=product_extractor_prompt, result_type = Product, *args, **kwargs):
        super().__init__(system_prompt=system_prompt, result_type=result_type, *args, **kwargs)

    async def run(self): ...

    
    async def __call__(
        self, 
        state: State, 
        config: dict = {}
    )-> Command[Literal[agent_manager.human_node, agent_manager.web_query_agent]]:
        # try:
        logger.info("reached writer agent node...")
        search_results = state['agent_results'][agent_manager.search_tool]
        print(search_results)
        user_id = state['user_id']

        model_to_use = state['model']

        model_config = self.get_model_config(model_to_use)

        all_products = []
        # try:
        #     await self.websocket_manager.send_progress(state['ws_id'], 'compiling', 0)
        # except Exception as e:
        #     logger.error(str(e), exc_info=True)

        logger.info('Started extraction')
        for search_result in search_results:
            await sleep(3)
            # Apply rate limiting
            # async with self.semaphore:
            logger.info("Calling LLM")
            result = await self.call_llm(
                user_id,
                str(search_result),
                type='text',
                model=model_config['model'],
                deps=model_config['deps']
            )
            logger.info("successfully calling LLM")
            # await self._wait_for_rate_limit()
            data: Product = result.data
            print(data)
            products = data.products
            if len(products) == 0:
                continue
            new_products = []
            for product in products:
                product_id = url_shortener.shorten_url(product.url)
                product = product.model_dump()
                product["product_id"] = product_id
                new_products.append(product)
        
            all_products.append(products)

        state['current_depth'] = state['current_depth'] + 1

        if all_products:
            await self.send_signals(state, '', products=all_products[:30])
            logger.info("Execuited Ultra search Writer agent")        
            return  Command(goto=agent_manager.human_node, update=state)    
        else:
            if state['max_depth'] > state['current_depth']:
                return Command(goto=agent_manager.human_node, update=state)  
            logger.info("No products found, going back to First Node")
            return   Command(goto=agent_manager.human_node, update=state)
        


writer_agent = UltraWriterAgent()
    