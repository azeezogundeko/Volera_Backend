import asyncio
from typing import Literal, List, Dict, Any, Optional, Union

# from fastapi import WebSocket, WebSocketDisconnect

from ..legacy.base import BaseAgent
from ..tools.search import search_tool
from ..config import agent_manager
from ..state import State
from .schema import Product, ProductDetail
from .prompt import product_extractor_prompt
from ..tools.rate_converter import CURRENCY_SYMBOLS, convert_currency, normalize_currency
from schema import ScrapingDependencies

from utils.logging import logger
# from ..legacy.llm import check_credits, track_llm_call

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
        self.word_threshold = 1000
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
    
    
    async def process_search_result(self, search_result, search_config, model_config, state, llm_semaphore):
        url = search_result['link']
        try:
            await self.websocket_manager.send_progress(
                state['ws_id'], status="comment", comment=f"Processing URL: {url}"
            )

            crawler = await self.get_crawler()
            results = await crawler.arun(url, config=self.crawler_config)

            state['agent_results'][agent_manager.research_agent]['n_scraped_items'] += 1
            await self.websocket_manager.send_progress(
                state['ws_id'],
                status="scraping",
                searched_items=state['agent_results'][agent_manager.research_agent]['n_scraped_items'],
            )
            
            markdown = self.get_markdown_content(results.markdown)
            if markdown is None:
                return None
            
            # self.rerank.chunk_rerank(
            #     query=search_config["query"] + " price name features product details",
            #     texts=markdown,
            # )

            # Determine if markdown is large enough to be chunked
            words = markdown.split()
            if len(words) > self.word_threshold:
                mid_index = len(markdown) // 2
                markdown_chunks = [markdown[:mid_index], markdown[mid_index:]]
            else:
                markdown_chunks = [markdown]

            page_contents = [
                {"Page URL": results.url, "Page Markdown": chunk} for chunk in markdown_chunks
            ]

            logger.info("Calling LLM for each markdown chunk concurrently")
            async with llm_semaphore:
                llm_tasks = [
                    self.call_llm(
                        user_id=state['user_id'],
                        user_prompt=str(page_content),
                        type='text',
                        model="google-gla:gemini-2.0-flash",
                        deps=ScrapingDependencies
                    ) for page_content in page_contents
                ]
                llm_responses = await asyncio.gather(*llm_tasks, return_exceptions=True)

            comments = []
            original_products = []
            for response in llm_responses:
                if isinstance(response, Exception) or not response.data.products:
                    continue
                comments.append("Research Agent: " + response.data.comment)
                original_products.extend(response.data.products)

            for comment in comments:
                await self.websocket_manager.send_progress(state['ws_id'], status="comment", comment=comment)

            if not original_products:
                return None

            logger.info('Preprocessing the results')
            await self.websocket_manager.send_progress(
                state['ws_id'], 
                status="comment", 
                comment=f"Research Agent: Preprocessing products for URL: {url}"
            )
            
            original_products = [product.model_dump() for product in original_products]
            original_products = await self.rerank.rerank(search_config['query'], original_products)

            products_dict = []
            for product in original_products:
                product['product_id'] = self.url_shoterner.shorten_url(url)
                products_dict.append(product)

            await self.websocket_manager.send_progress(
                state['ws_id'], 
                status="comment", 
                comment=f"Research Agent: Finished processing URL: {url}"
            )
            return products_dict



        except Exception as e:
            logger.error(e, exc_info=True)
            await self.websocket_manager.send_progress(
                state['ws_id'], 
                status="comment", 
                comment=f"Research Agent: Error processing URL: {url}"
            )
            return None

    async def run(self, state: State, config: dict = {}):
        logger.info("Reached Research Agent")
        planner_agent_results = state["agent_results"][agent_manager.planner_agent]
        # print(planner_agent_results)
        research_agent_result = state["agent_results"].get(agent_manager.research_agent, None)

        if research_agent_result is None:
            research_agent_result = self.get_agent_results(state)

        model_config = self.get_model_config(state['model'])
        current_products = []
        # search_config = self.get_search_query(state)
        for search_config in planner_agent_results['content']['search_queries']:
            logger.info(f"Search Query: {search_config}")

            agent_results = state['agent_results'][agent_manager.research_agent]
            # if search_config is None:
            #     raise ValueError("No more queries available for search.")

            await self.websocket_manager.send_progress(
                state['ws_id'], 
                status="comment", 
                comment=f"Research Agent: Searching products for query: {search_config}"
            )

            search_query = f"{search_config['query']} {search_config['site']}"

            search_results = await self.search_tool.search_products(query=search_query, num_results=2)
            # print(search_results)
            await self.websocket_manager.send_progress(
                state['ws_id'], 
                status="searching", 
                searched_items=len(search_results)
            )
            products = agent_results.get('all_products', [])
            

            # Create a semaphore to limit the number of concurrent LLM calls (e.g., 5 at a time)
            llm_semaphore = asyncio.Semaphore(2)

            # Create tasks for processing each search result concurrently
            tasks = [
                self.process_search_result(search_result, search_config, model_config, state, llm_semaphore)
                for search_result in search_results
            ]
            # Gather results concurrently
            results = await asyncio.gather(*tasks)

            # Filter out None results and combine all product dictionaries
            for product_dicts in results:
                if product_dicts:
                    products.extend(product_dicts)
                    current_products.extend(product_dicts)

            logger.info(f'Number of searched products are {len(products)}')
            logger.info(f'Number of Current searched products are {len(current_products)}')

            # try:
        #     products = await self.preprocess_currencies(products)
        # except Exception as e:
        #     logger.error(e, exc_info=True)

        # Update state with results and notify final progress
        # products = self.filter_products(planner_agent_results, products)
        state['agent_results'][agent_manager.research_agent]["current_products"] = current_products
        state['agent_results'][agent_manager.research_agent]["all_products"] = products
        logger.info(f'Total number of current searched products are {len(products)}')
        logger.info('Navigating to Reviewer Agent')
        return Command(goto=agent_manager.reviewer_agent, update=state)



    async def __call__(self, state: State, config={}) -> Command[
        Literal[agent_manager.reviewer_agent, agent_manager.planner_agent]]:
        try:
            await self.run(state, config)
        except Exception as e:
            # if "No more queries" in str(e):
            state['human_response'] = "An error occured, can you try a new plan"
            await self.websocket_manager.send_progress(
                state['ws_id'], 
                status="comment", 
                comment="No results for Query, Creating a new plan"
            )
            logger.info("Going back to planner agent")
            return Command(goto=agent_manager.planner_agent, update=state)

        return Command(goto=agent_manager.reviewer_agent, update=state)
    
    
    def get_search_query(self, state: State):
        planner_agent_results = state["agent_results"][agent_manager.planner_agent]
        research_agent_result = state["agent_results"].get(agent_manager.research_agent, None)

        if research_agent_result is None:
            research_agent_result = self.get_agent_results(state)

        # Get the list of already searched queries (each a dict with 'site' and 'query')
        searched_queries = research_agent_result.get("searched_queries", [])
        # Build a set of (site, query) tuples for fast lookup
        searched_set = {(item.get('site'), item.get('query')) for item in searched_queries}

        # 'queries_to_search' is a list of dicts with keys 'site' and 'query'
        queries_to_search = planner_agent_results['content']['search_queries']

        query_to_search = None
        # Find the first query item that hasn't been searched (comparing both site and query)
        for query_item in queries_to_search:
            key = (query_item.get('site'), query_item.get('query'))
            if key not in searched_set:
                query_to_search = query_item
                break

        if query_to_search is None:
            # No more queries available; you can decide to either return None or raise an exception
            return None

        # Append the current search query (the whole dict) to the list of searched queries
        searched_queries.append(query_to_search)
        state["agent_results"][agent_manager.research_agent]['searched_queries'] = searched_queries

        return query_to_search
    

    def filter_products(planner_agent_results, products):
        search_configs = planner_agent_results["content"]["search_queries"]

        sources = [search_config["source"].lower() for search_config in search_configs]
        filtered_products = []

        for product in products:
            if product['source'].lower() not in sources:
                continue

            filtered_products.append(product)

        return filtered_products


    
    def get_crawler_config(self):
        bm25_filter = BM25ContentFilter(
            user_query="price name features product details",  # tailored query
            bm25_threshold=1.2  # higher value for stricter, more relevant matches
        )
        md_generator = DefaultMarkdownGenerator()
        
        config = CrawlerRunConfig(
            # word_count_threshold=3,  # allow even short text blocks typical of product info
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
    
    def get_markdown_content(self, content) -> Optional[str]:
        if content is None:
            return None
        # if isinstance(content, MarkdownGenerationResult):
        # else:
        #     return content.markdown
        return content




researcher_agent = ResearchAgent()
