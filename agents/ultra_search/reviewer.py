import asyncio
from typing import Literal, List

# from fastapi import WebSocket, WebSocketDisconnect

from ..legacy.base import BaseAgent
from ..config import agent_manager
from ..state import State
from .schema import ReviewerSchema
from .prompt import reviewer_system_prompt

from utils.logging import logger
# from ..legacy.llm import check_credits, track_llm_call

from schema import extract_agent_results

from langgraph.types import Command


class ReviewerAgent(BaseAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(
            model='google-gla:gemini-2.0-flash-exp',
            result_type=ReviewerSchema, 
            system_prompt=reviewer_system_prompt, 
            name=agent_manager.reviewer_agent)
        

    @extract_agent_results(agent_manager.reviewer_agent)
    async def run(self, state: State, config: dict={}):
        research_agent_results = state['agent_results'][agent_manager.research_agent]
        planner_agent_results = state['agent_results'][agent_manager.planner_agent]['content']
        # print(planner_agent_results)
        instructions = planner_agent_results['researcher_agent_instructions']
        filter_criteria = planner_agent_results['filter_criteria']
        user_query = state['ws_message']['content']
        current_products = research_agent_results['current_products']
        print(len(current_products))
        model_config = self.get_model_config(state['model'])

        user_prompt = {
            'Instructions': instructions,
            'filter criteria': filter_criteria, 
            'Current Products': current_products,
        }

        response = await asyncio.wait_for(self.call_llm(
            user_id=state['user_id'],
            user_prompt=str(user_prompt),
            type='text',
            model=model_config['model'],
            deps=model_config['deps']
        ),
        timeout=60      
        )
        logger.info('Called the Reviewer agent')
        # logger.info('Status: ', response.data.status)
        return response
    

    async def __call__(self, state: State, config: dict = {})-> Command[
        Literal[agent_manager.human_node, agent_manager.research_agent, agent_manager.summary_agent]
        ]:
        try:
            research_agent_results = state['agent_results'][agent_manager.research_agent]
            planner_agent_results = state['agent_results'][agent_manager.planner_agent]['content']
            # all_products = research_agent_results['all_products']

            agent_response = await self.run(state, config)
        

            result: ReviewerSchema = agent_response.data
            

            await self.websocket_manager.send_progress(state['ws_id'], status="comment", comment=result.comment)

            if state['current_depth'] > state['max_depth']:
                await self.websocket_manager.send_progress(state['ws_id'], status="comment", comment='Max depth reached for research, gathering all searched items')
                logger.info('Max depth reached for ultra search')
                return Command(goto=agent_manager.summary_agent, update=state)

            state['current_depth'] += 1

            logger.info(f'Current Depth {state['current_depth']}')
            if result.status == '__failed__':
                state['human_response'] = "The Current plan failed to pass, can you try a new plan"
                logger.info("Products failed to meet requirements, Goining back to new Research Agents")
                return Command(goto=agent_manager.planner_agent, update=state)
            
            # Ensure the key exists before modifying the list
            reviewed_products = state['agent_results'].setdefault(agent_manager.research_agent, {}).setdefault('reviewed_products_ids', [])

            # Extend the reviewed products list
            state['agent_results'][agent_manager.research_agent]["reviewed_products_ids"].extend(result.product_ids)
            await self.websocket_manager.send_progress(
                    state['ws_id'], 
                    status="comment", 
                    comment=f"Reviewer Agent: Total numbers of reviewed Items {len(research_agent_results["reviewed_products_ids"])}"
                )
            logger.info(f'Total numbers of reviewed Items {len(research_agent_results["reviewed_products_ids"])}')
            # Check if we need to continue reviewing or proceed to sending the final response
            if len(reviewed_products) < planner_agent_results['no_of_results']:
                await self.websocket_manager.send_progress(
                    state['ws_id'], 
                    status="comment", 
                    comment=f"Reviewer Agent: Products are passed but insufficients numbers, searching more..."
                )
                state['human_response'] = "I need more results, Can you try a new plan to provide more results"
                logger.info("Products are passed but insufficients numbers, searching more...")
                return Command(goto=agent_manager.planner_agent, update=state)

            return Command(goto=agent_manager.summary_agent, update=state)

        except Exception as e:
            logger.error(e, exc_info=True)


        
        
    def filter_products(self, state, product_ids: List[str]):
        research_agent_results = state.get('agent_results', {}).get(agent_manager.research_agent, {})
        all_products = research_agent_results.get("all_products", [])

        # Filter products based on product_ids
        products = [product for product in all_products if product.get('product_id') in product_ids]

        # Sort products by relevance_score in descending order
        products.sort(key=lambda product: product.get('relevance_score', 0), reverse=True)

        return products



        
reviewer_agent = ReviewerAgent()






        


    