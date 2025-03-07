import asyncio
from typing import Literal, List, Dict, Any

# from fastapi import WebSocket, WebSocketDisconnect

from ..legacy.base import BaseAgent
from ..tools.search import search_tool
from ..config import agent_manager
from ..state import State
from .schema import Product, ProductDetail
from .prompt import product_extractor_prompt
from ..tools.rate_converter import CURRENCY_SYMBOLS, convert_currency, normalize_currency

from utils.logging import logger
from ..legacy.llm import check_credits, track_llm_call

from langgraph.types import Command
from crawl4ai import CrawlerRunConfig, BM25ContentFilter, DefaultMarkdownGenerator


class ResearchAgent(BaseAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(
            model='google-gla:gemini-2.0-flash-exp',
            name=agent_manager.research_agent,
            system_prompt=product_extractor_prompt,
            result_type=Product,
            **kwargs
            )
        self.crawler_config = self.get_crawler_config()


    def get_agent_results(self, state: State):
        agent_result = state['agent_results'][agent_manager.research_agent] = {
            "all_products": [],
            "current_products": [],
            "searched_queries": [],
            "user_query": "",
            "reviewed_products_ids": [],
            "n_scraped_items": 0,
            'n_searched_items': 0
        }
        return agent_result
    
    def get_search_query(self, state: State):
        planner_agent_results = state["agent_results"][agent_manager.planner_agent]
        research_agent_result = state["agent_results"].get(agent_manager.research_agent, None)

        if research_agent_result is None:
            research_agent_result = self.get_agent_results(state)

        searched_queries = research_agent_result.get("searched_queries", [])
        
        query_to_search = None
        print(planner_agent_results)
        queries_to_search = planner_agent_results['content']['search_queries']

        for query in queries_to_search:
            if query not in searched_queries:
                query_to_search = query
                break  # Stop at the first unsued query

        # if query_to_search is None:
        #     # No more items to search - raise an appropriate exception
        #     raise Exception("No more queries available for search.")

        searched_queries.append(query_to_search)
        state["agent_results"][agent_manager.research_agent]['searched_queries'] = searched_queries

        return query_to_search

    async def run(self, state: State, config: dict = {}):

        logger.info("Reached Research Agent")
        search_query = self.get_search_query(state)
            
        logger.info(f"Search Query: {search_query}")
        model_config = self.get_model_config(state['model'])

        agent_results = state['agent_results'][agent_manager.research_agent]
        n_scraped = agent_results['n_scraped_items']
        n_searched = agent_results['n_searched_items']
        if search_query is None:
            raise ValueError("No more queries available for search.")
            # maybe tell the user we could not find relevant products or go back to planner agent
        
        search_results = await self.search_tool.search_products(search_query)

        try:
            products = state['agent_results'][agent_manager.research_agent]['all_products']
            current_products = []
            

            for search_result in search_results:
                url = search_result['link']

                crawler = await self.get_crawler()
                results = await crawler.arun(url, config=self.crawler_config)

                n_scraped += 1
                await self.websocket_manager.send_progress(state['ws_id'], status="scraping", searched_items=n_scraped)

                if not results.success:
                    continue


                markdown = results.markdown_v2
                if markdown is None:
                    continue

                markdown = {
                    "Page URL": results.url,
                    "Page Markdown": markdown
                }

                logger.info("Calling LLM")
                try:
                    llm_response = await self.call_llm(
                        user_id=state['user_id'],
                        user_prompt=str(markdown),
                        type='text',
                        model=model_config['model'],
                        deps=model_config['deps']
                    )
                except Exception as e:
                    logger.error(e, exc_info=True)
                    continue

                await self.websocket_manager.send_progress(state['ws_id'], status="comment", comment=llm_response.data.comment)
                if len(llm_response.data.products) == 0:
                    continue
                
                logger.info('Preprocessing the results')
                original_products: List[ProductDetail]= llm_response.data.products
                original_products = [product.model_dump() for product in original_products]
                original_products = await self.rerank.rerank(search_query, original_products)
                original_products = original_products[:30]
                logger.info('Finished preprocessing the results')

                products_dict = []
                for product in original_products:
                    product['product_id'] = self.url_shoterner.shorten_url(url)
                    products_dict.append(product)


                products.extend(products_dict)

                try:
                    logger.info('Converting all prices to naira')
                    products = await self.preprocess_currencies(products)
                except Exception as e:
                    logger.error(e, exc_info=True)

                current_products.extend(products_dict)
                print('Searched products: ', products_dict)
                # await asyncio.sleep(3)
                # crawl and extract the markdown
                # pass markdown to llm if successfully crawled
                # route to reviewer agent to analyse the results
                # if all conditions are met results are returned to user else back to research agent to get more results

            logger.info('Storing the results')
            state['agent_results'][agent_manager.research_agent]['n_scraped_items'] = n_scraped
            state['agent_results'][agent_manager.research_agent]['all_products'] = products
            state['agent_results'][agent_manager.research_agent]['current_products'] = current_products

            # Go to Reviewer agent to see if all conditions have been met
            logger.info('Navigating to Reviewer Agent')
            return Command(goto=agent_manager.reviewer_agent, update=state)
        except Exception as e:
            logger.error(e, exc_info=True)


    async def __call__(self, state: State, config={}) -> Command[
        Literal[agent_manager.reviewer_agent, agent_manager.planner_agent]]:
        try:
            await self.run(state, config)
        except ValueError as e:
            if "No more queries" in str(e):
                state['human_response'] = "No searched products, can you try a new plan"
                logger.info("Going back to planner agent")
                return Command(goto=agent_manager.planner_agent, update=state)

        return Command(goto=agent_manager.reviewer_agent, update=state)

    
    def get_crawler_config(self):
        bm25_filter = BM25ContentFilter(
            user_query="price name features product details",  # tailored query
            bm25_threshold=1.2  # higher value for stricter, more relevant matches
        )
        md_generator = DefaultMarkdownGenerator(content_filter=bm25_filter)
        
        config = CrawlerRunConfig(
            word_count_threshold=3,  # allow even short text blocks typical of product info
            excluded_tags=["nav", "footer", "header", "script", "style"],  # remove boilerplate
            exclude_external_links=True,
            markdown_generator=md_generator,
            magic=True,
            bypass_cache=True
        )
        return config
    
    async def preprocess_currencies(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        tasks = []
        
        for product in products:
            currency_symbol = product['currency']
            amount = product['current_price']
            currency_code = CURRENCY_SYMBOLS.get(currency_symbol, currency_symbol.lower())
            
            if currency_code == 'ngn':
                continue
            
            tasks.append(convert_currency(amount=amount, from_currency=currency_code, to_currency='ngn'))
        
        results = await asyncio.gather(*tasks)
        
        for product, converted_price in zip(products, results):
            if converted_price is not None:
                product['converted_price'] = converted_price
                product['converted_currency'] = 'ngn'
        
        return products




researcher_agent = ResearchAgent()
