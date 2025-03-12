from typing import Literal

from .prompts.web_prompts import web_response_prompt
from ..writer import WriterAgent
from ..state import State
from ..config import agent_manager
from ..tools.markdown import convert_to_markdown
from schema import extract_agent_results
from utils.websocket import ImageMetadata, SourceMetadata
from utils.logging import logger

from langgraph.types import Command
from pydantic_ai.result import ResultDataT
from langgraph.store.base import BaseStore


class WebWriterAgent(WriterAgent):
    def __init__(self, system_prompt=web_response_prompt, *args, **kwargs):
        super().__init__(system_prompt=system_prompt,*args, **kwargs)

    @extract_agent_results(agent_manager.writer_agent)
    async def run(self,state: State, user_input: str | None = None) -> ResultDataT:
        user_id = state.get("user_id")
        if not user_id:
            raise ValueError("User ID not found in state")
        search_result = state["agent_results"][agent_manager.search_tool]
        search = search_result["search"]

        previous_messages = state["message_history"]

        if user_input is None:
            user_input = state["ws_message"]["message"]["content"]


        prompt = {
            "User Input": user_input,
            "Search Results": search,
            # "Memory from past Conversation": memories
        }
        state["previous_node"] = agent_manager.writer_agent
        state["next_node"] = agent_manager.web_query_agent

        model_config = self.get_model_config(state["model"])

        response = await self.call_llm(
            user_id=user_id, 
            type='text', 
            user_prompt=str(prompt),
            deps=model_config["deps"],
            model=model_config["model"]
            )
        state["message_history"] = previous_messages + response.new_messages()
        return response

    async def __call__(self, state: State, config={}, * store: BaseStore) -> Command[
        Literal[agent_manager.end, agent_manager.human_node]]:
            
        user_input = state["human_response"] if "human_response" in state else None
        response = await self.run(state, user_input)
        content = convert_to_markdown(response.data.content)
        ws_id = state["ws_id"]
        sources, images = self.extract_results(state)
       
        await self.send_signals(
            state,
            content=content,
            images=images,
            sources=sources,
            # products=product_data
        )

        # await self.evaluate_chat_limit(state)
        logger.info("Continuing conversation for follow-up questions")
        return Command(goto=agent_manager.end, update=state)


    def extract_results(self, state: State) -> ResultDataT:
        images = []
        sources = []

        search_results = state["agent_results"][agent_manager.search_tool]
        for r in search_results["image"]:
            images.append(
                ImageMetadata(
                    url=r["link"],
                    img_url=r["image_url"],
                    title=r["thumbnail"],
                    # favicon=r["metadata"].get("image_url", ""),
                )
            )
            # image_files.append(r["image_url"])
        for r in search_results["search"]:
            sources.append(
                SourceMetadata(
                    url=r["link"],
                    content=r["snippet"],
                    title=r["title"]
                )
            )

        state["images"] = images
        state["sources"] = sources

        return sources, images

web_writer_agent_node = WebWriterAgent()