import asyncio
from typing import Literal, List, Dict, Any

# from fastapi import WebSocket, WebSocketDisconnect

from ..legacy.base import BaseAgent
from ..config import agent_manager
from ..state import State
from .schema import ResponseSchema
from .prompt import response_system_prompt

from utils.logging import logger
# from ..legacy.llm import check_credits, track_llm_call

from schema import extract_agent_results

from langgraph.types import Command



class ResponseAgent(BaseAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(
            model='google-gla:gemini-2.0-flash-exp',
            result_type=ResponseSchema, 
            system_prompt=response_system_prompt, 
            name=agent_manager.summary_agent
            )

    @extract_agent_results(agent_manager.summary_agent)  
    async def run(self, state: State, config: Dict[str, Any]):
        research_agent_results = state['agent_results'][agent_manager.research_agent]
        planner_agent_results = state['agent_results'][agent_manager.planner_agent]['content']

        user_input = state['ws_message']['content']

        n_results = planner_agent_results["no_of_results"]
        all_products = research_agent_results["all_products"]
        reviewed_products_ids = research_agent_results["reviewed_products_ids"]

        prompt = {
            "User Query": user_input,
            "Final Number of Results Outputs Wanted": n_results,
            "Passed/Reviewed Products ID":  reviewed_products_ids,
            "Searched Product Database": all_products,

        }
        model_config = self.get_model_config(state['model'])

        response = await self.call_llm(
            user_id=state['user_id'],
            user_prompt=str(prompt),
            deps=model_config['model'],
            model=model_config['model'],
            type="text"

        )

        return response

    async def __call__(self, state: State, config: Dict[str, Any] = {}) -> Command[Literal[agent_manager.human_node]]:
        try:
            response = await self.run(state, config)

            result: ResponseSchema = response.data

            await self.websocket_manager.send_progress(
                        state['ws_id'], 
                        status="comment", 
                        comment=f"Response Agent: {result.comment}"
                    )
            
            product_ids = result.product_ids
            filtered_products = None
            if product_ids:
                filtered_products = self.filter_products(state, product_ids)

            return await self.go_to_user_node(
                state, 
                ai_response=result.response, 
                products=filtered_products, 
                go_back_to_node=agent_manager.planner_agent
                )
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
    

response_agent = ResponseAgent()