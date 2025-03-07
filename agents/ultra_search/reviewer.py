import asyncio
from typing import Literal, List

# from fastapi import WebSocket, WebSocketDisconnect

from ..legacy.base import BaseAgent
from ..config import agent_manager
from ..state import State
from .schema import ReviewerSchema
from .prompt import reviewer_system_prompt

from utils.logging import logger
from ..legacy.llm import check_credits, track_llm_call
from schema import extract_agent_results

from langgraph.types import Command


class ReviewerAgent(BaseAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(
            model='google-gla:gemini-2.0-flash-exp',
            result_type=ReviewerSchema, 
            system_prompt=reviewer_system_prompt, 
            name=agent_manager.reviewer_agent)
        
    async def price_converter(value, currency: str): ...
        


    @extract_agent_results(agent_manager.reviewer_agent)
    async def run(self, state: State, config: dict={}):
        research_agent_results = state['agent_results'][agent_manager.research_agent]
        planner_agent_results = state['agent_results'][agent_manager.planner_agent]['content']
        # print(planner_agent_results)
        instructions = planner_agent_results['researcher_agent_instructions']
        filter_criteria = planner_agent_results['filter_criteria']
        user_query = research_agent_results['user_query']
        current_products = research_agent_results['current_products']
        model_config = self.get_model_config(state['model'])

        user_prompt = {
            'Instructions': instructions,
            'filter criteria': filter_criteria, 
            'Products': current_products,
            "User Query": user_query,
        }

        response = await self.call_llm(
            user_id=state['user_id'],
            user_prompt=str(user_prompt),
            type='text',
            model=model_config['model'],
            deps=model_config['deps']
        )
        logger.info('Called the Reviewer agent')
        # logger.info('Status: ', response.data.status)
        return response
    

    async def __call__(self, state: State, config: dict = {})-> Command[
        Literal[agent_manager.human_node, agent_manager.research_agent]
        ]:

        agent_response = await self.run(state, config)
        result: ReviewerSchema = agent_response.data

        await self.websocket_manager.send_progress(state['ws_id'], status="comment", comment=result.comment)

        if result.status == '__failed__':
            logger.info("Products failed to meet requirements, Goining back to new Research Agents")
            return Command(goto=agent_manager.research_agent, update=state)
        
        try:
            # Ensure the key exists before modifying the list
            reviewed_products = state['agent_results'].setdefault(agent_manager.research_agent, {}).setdefault('reviewed_products_ids', [])

            # Extend the reviewed products list
            reviewed_products.extend(result.product_ids)

            # Check if we need to continue reviewing or proceed to sending the final response
            if len(reviewed_products) < 25:
                return Command(goto=agent_manager.research_agent, update=state)

            # Filter the products that match the reviewed product IDs
            filtered_products = self.filter_products(state, result.product_ids)

            # Log before sending response
            logger.info("Sending final response to user")

            # Send the final signal with error handling
            try:
                await self.send_signals(state, products=filtered_products)
            except Exception as e:
                logger.error(f"Failed to send signals: {e}")

        except Exception as e:
            logger.error(e, exc_info=True)

        return Command(goto=agent_manager.human_node, update=state)

        
        
    def filter_products(state, product_ids: List[str]):
        research_agent_results = state.get('agent_results', {}).get(agent_manager.research_agent, {})
        all_products = research_agent_results.get("all_products", [])

        return [product for product in all_products if product.get('product_id') in product_ids]


        
reviewer_agent = ReviewerAgent()






        


    