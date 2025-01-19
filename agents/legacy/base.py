# from abc import ABC
from typing import Literal, TypeVar, Optional, List

from ..config import agent_manager
from prompts import (
    search_agent_prompt, 
    policy_assistant_prompt, 
    planner_agent_prompt
    )
from schema.dataclass.dependencies import GroqDependencies, GeminiDependencies, BaseDependencies
from schema.validations.agents_schemas import( 
    FeedbackResponseSchema,
    PlannerAgentSchema, 
    SearchAgentSchema, 
    ComparisonSchema,
    MetaAgentSchema,
    InsightsSchema,
    ReviewerSchema,
    PolicySchema,
    HumanSchema,
    WebSchema,
    )

from ..state import State
from config import DB_PATH
from utils.websocket import WebSocketManager, ImageMetadata, ProductSchema, SourceMetadata
from utils.background import background_task
from utils.ecommerce_manager import EcommerceManager
from schema.dataclass.decourator import extract_agent_results
from utils.db_manager import ProductDBManager

from pydantic_ai import Agent
from langgraph.types import Command
from pydantic_ai.result import RunResult
from schema.validations.agents_schemas import BaseSchema

BaseSchemaType = TypeVar('BaseSchemaType', bound=BaseSchema)

class BaseAgent:
    def __init__(
        self, 
        name: str,
        model: str,
        system_prompt: str,
        result_type: BaseSchemaType,
        deps_type: BaseDependencies,
        timeout:int = 10,
        retries: int = 3,
    ):
        self.timeout = timeout
        self.agent_name = name
        self.background_task = background_task
        
        self.websocket_manager = WebSocketManager()
        self.llm = Agent(
            name=name,
            model=model,
            system_prompt=system_prompt,
            deps_type=deps_type,
            result_type=result_type,
            retries=retries
        )

    async def list_product(
        self, 
        query: str, 
        limit: int= 5, 
        page: int = 1, 
        max_results: int = 5,
        site: Literal["all", "jumia.com.ng", "jiji.ng", "konga.com"] = "all",
        bypass_cache: bool = False,
        sort: Optional[str] = None,
        filters: dict = None

        ):
        from api.product.services import list_products

        # seems this was called before app started so put it here so that main take initialization
        # Using Singleton design pattern
        self._ecommerce_manager = EcommerceManager(ProductDBManager(DB_PATH))
        
        return await list_products(
            self._ecommerce_manager, 
            query, 
            site,
            max_results,
            bypass_cache,
            page,
            limit,
            sort,
            filters 
            )

    def get_message_data(self, chat_id: str, type: str,  sources=None, images=None, products=None, content=None):
        return {
                "role": "assistant",
                "chat_id": chat_id,
                "images": images,
                "products": products,
                "sources": sources,
                "type": type,
                "content": content
            }

    async def send_signals(
        self, 
        state: State,
        content: str,
        images: List[ImageMetadata] = None,
        sources: List[SourceMetadata] = None,
        products : List[ProductSchema] = None        
        )-> None:
            
        
        ws_id = state["ws_id"]
        message = state["ws_message"]
        chat_id= message["chat_id"]
        message_id= message["message_id"]  

        data = {
            "role": "assistant",
            "chat_id": chat_id,
            "images": images,
            "products": products,
            "sources": sources,
            "type": "message",
            "content": content
        }

        await self.websocket_manager.send_json(ws_id, data)
        await self.websocket_manager.send_json(ws_id, data)


        source_data= None
        image_data=None
        product_data=None
        
        
        if sources is not None:
            source_data = [str(source) for source in sources]
            # await self.websocket_manager.send_sources(ws_id, sources)

        if images is not None:
            image_data = [str(image) for image in images]
            # await self.websocket_manager.send_images(ws_id, images)


        if products is not None:
            product_data = [str(product) for product in products]
            # await self.websocket_manager.send_product(ws_id, message_id, chat_id, products)
         

        message_data = self.get_message_data(
            chat_id,
             "message", 
             content=content, 
             sources=source_data, 
             images=image_data, 
             products=product_data
        )
        state["message_data"] = message_data


    @extract_agent_results
    async def run(self) -> RunResult:
        raise NotImplementedError

    async def __call__(self, state: State, config: dict = {}) -> BaseSchemaType:
        raise NotImplementedError

    async def evaluate_chat_limit(self, state: State):
        CHAT_LIMIT_MESSAGES = [
        "Thank you for your engaging questions! We've reached the end of our session. Feel free to start a new conversation anytime.",
        "I've enjoyed helping you today! For a fresh perspective, let's start a new conversation.",
        "We've had a great discussion! To ensure the best experience, please start a new session for more questions.",
        "Thanks for the wonderful interaction! To continue exploring, please begin a new chat session.",
        "It's been a pleasure assisting you! For more questions, feel free to start a fresh conversation.",
        "We've covered quite a bit today! For optimal assistance, let's continue in a new session.",
        "Thank you for your thoughtful questions! To maintain quality, please start a new conversation.",
        "I've enjoyed our productive session! For further assistance, let's begin anew.",
        "We've had an informative exchange! For the best experience, please initiate a new chat.",
        "Thanks for engaging with me! To continue our discussion, let's start fresh.",
        "It's been great helping you today! For more insights, please begin a new session.",
        "We've explored many topics! For continued assistance, let's start a new conversation.",
        "Thank you for your interest! For optimal support, please initiate a fresh session.",
        "I've enjoyed our discussion! For more questions, let's begin anew.",
        "We've had a meaningful exchange! Please start a new session for further assistance.",
        "Thanks for your questions! For the best experience, let's continue in a fresh conversation.",
        "It's been a pleasure chatting! For more help, please start a new session.",
        "We've covered several topics today! For continued support, let's begin fresh.",
        "Thank you for your engagement! For optimal assistance, please start a new conversation.",
        "I've enjoyed helping you! For more questions, let's start a new session together."
    ]
        chat_limit = state["chat_limit"]
        chat_count = state["chat_count"]
        chat_finished = state["chat_finished"]

        if chat_count >= chat_limit or chat_finished:
            import random
            end_message = random.choice(CHAT_LIMIT_MESSAGES)
            await self.websocket_manager.stream_final_response(state["ws_id"], end_message)
            return Command(goto=agent_manager.end, update=state)

        state["chat_count"] = chat_count + 1
























def create_meta_agent(prompt)-> Agent:
    return Agent(
            name=agent_manager.meta_agent,
            retries=3,
            system_prompt=prompt,
            model="gemini-1.5-flash",
            deps_type=GeminiDependencies,
            result_type=MetaAgentSchema,
        )

def create_planner_agent()-> Agent:
    return Agent(
            name=agent_manager.planner_agent,
            retries=3,
            system_prompt=planner_agent_prompt,
            model="gemini-2.0-flash-exp",
            deps_type=GeminiDependencies,
            result_type=PlannerAgentSchema,
        )
def create_copilot_agent(prompt)-> Agent:
    return Agent(
            name=agent_manager.copilot_mode,
            retries=3,
            system_prompt=prompt,
            model="gemini-2.0-flash-exp",
            deps_type=GeminiDependencies,
            result_type=FeedbackResponseSchema,
        )

def create_search_agent():
    return Agent(
                name=agent_manager.search_agent,
                retries=3,
                system_prompt=search_agent_prompt,
                model="gemini-1.5-flash",
                deps_type=GeminiDependencies,
                result_type=SearchAgentSchema
            )

def create_insights_agent(prompt):
    return Agent(
                name=agent_manager.insights_agent,
                retries=3,
                system_prompt=prompt,
                model="groq:llama3-groq-70b-8192-tool-use-preview",
                deps_type=GroqDependencies,
                result_type=InsightsSchema
            )

def create_policy_agent()-> Agent:  
    return Agent(
            name=agent_manager.policy_agent,
            retries=3,
            system_prompt=policy_assistant_prompt,
            model="groq:llama3-70b-8192",
            deps_type=GroqDependencies,
            result_type=PolicySchema
        )

def create_human_agent(prompt)-> Agent:  
    return Agent(
            name=agent_manager.human_node,
            retries=3,
            system_prompt=prompt,
            model="gemini-1.5-flash",
            deps_type=GeminiDependencies,
            result_type=HumanSchema
        )

# writer_agent = Agent(
#             name=agent_manager.meta_agent,
#             retries=3,
#             system_prompt=insights_prompt,
#             model=model,
#             deps_type=...,
#         )


def create_reviewer_agent(prompt)-> Agent:
    return Agent(
        name=agent_manager.reviewer_agent,
        retries=3,
        system_prompt=prompt,
        model="groq:llama3-70b-8192",
        deps_type=GroqDependencies,
        result_type=ReviewerSchema
    )

def create_web_agent(prompt)-> Agent:
    return Agent(
        name=agent_manager.reviewer_agent,
        retries=3,
        system_prompt=prompt,
        model="groq:llama3-70b-8192",
        deps_type=GroqDependencies,
        result_type=WebSchema
    )

def create_writer_agent(prompt)-> Agent:
    return Agent(
        name=agent_manager.writer_agent,
        retries=3,
        system_prompt=prompt,
        model="gemini-2.0-flash-exp",
        deps_type=GeminiDependencies,
        result_type=ReviewerSchema
    )

# shop_agent = Agent(
#             name=agent_manager.meta_agent,
#             retries=3,
#             system_prompt="",
#             model=model,
#             deps_type=...,
#         )

# memory_agent = Agent(
#             name=agent_manager.meta_agent,
#             retries=3,
#             system_prompt="",
#             model=model,
#             deps_type=...,
#         )

def create_comparison_agent(prompts)-> Agent:
    return Agent(
        name=agent_manager.comparison_agent,
        retries=3,
        system_prompt=prompts,
        model="groq:llama3-70b-8192",
        deps_type=GroqDependencies,
        result_type=ComparisonSchema
    )
