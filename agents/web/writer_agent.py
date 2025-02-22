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
from pydantic_ai.result import RunResult


class WebWriterAgent(WriterAgent):
    def __init__(self, system_prompt=web_response_prompt, *args, **kwargs):
        super().__init__(system_prompt=system_prompt,*args, **kwargs)

    @extract_agent_results(agent_manager.writer_agent)
    async def run(self,state: State, user_input: str = None) -> RunResult:
        search_result = state["agent_results"][agent_manager.search_tool]
        search = search_result["search"]

        previous_messages = state["message_history"]

        if user_input is None:
            user_input = state["ws_message"]["message"]["content"]

        prompt = {
            "User Input": user_input,
            "Search Results": search
        }
        state["previous_node"] = agent_manager.writer_agent
        state["next_node"] = agent_manager.web_query_agent

        response = await self.llm.run(str(prompt))
        state["message_history"] = previous_messages + response.new_messages()
        return response

    async def __call__(self, state: State, config={}) -> Command[
        Literal[agent_manager.end, agent_manager.human_node]]:
            
        user_input = state["human_response"] if "human_response" in state else None
        response = await self.run(state, user_input)
        content = convert_to_markdown(response.data.content)
        ws_id = state["ws_id"]
        sources, images = self.extract_results(state)

        task_id = state["task_id"]
        product_data = None

        try:
            value = self.background_task.is_task_done(task_id)
            if value is False:
                await self.websocket_manager.send_progress(ws_id, "searching", 0)
                results = await self.background_task.wait_for_completion(task_id)
                product_data = results

            else:
                product_data = self.background_task.get_result(task_id)
                    
        except ValueError as e:
            logger.error(f"Error Retrieving Task {task_id}: {e}")
        
        await self.send_signals(
            state,
            content=content,
            images=images,
            sources=sources,
            products=product_data
        )

        await self.evaluate_chat_limit(state)
        logger.info("Continuing conversation for follow-up questions")
        return Command(goto=agent_manager.human_node, update=state)


    def extract_results(self, state: State) -> RunResult:
        images = []
        sources = []

        search_results = state["agent_results"][agent_manager.search_tool]
        for r in search_results["image"]:
            images.append(
                ImageMetadata(
                    url=r["link"],
                    img_url=r["link"],
                    title=r["title"],
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