from ..web.writer_agent import WebWriterAgent
from utils.websocket import SourceMetadata, ImageMetadata

from pydantic_ai.result import RunResult
from .prompts.writer_prompt import writer_response_prompt
from ..state import State
from schema import extract_agent_results
from ..config import agent_manager


class InsightsWriterAgent(WebWriterAgent):
    def __init__(self, system_prompt=writer_response_prompt, *args, **kwargs):
        super().__init__(system_prompt=system_prompt, *args, **kwargs)


    @extract_agent_results(agent_manager.writer_agent)
    async def run(self,state: State, user_input: str = None) -> RunResult:
        search_result = state["agent_results"][agent_manager.search_tool]
    

        if user_input is None:
            user_input = state["ws_message"]["message"]["content"]

        prompt = {
            "User Input": user_input,
            "Search Results": search_result["search"]
        }

        response = await self.llm.run(str(prompt))

        state["next_node"] = agent_manager.followup
        state["previous_node"] = agent_manager.writer_agent

        return response

    def extract_results(self, state: State):
        images = []
        sources = []
        search_result = state["agent_results"][agent_manager.search_tool]
        optimization_mode = state["ws_message"]["optimization_mode"]

        if optimization_mode == "fast":
            for r in search_result["search"]:
                sources.append(
                    SourceMetadata(
                        url=r["link"],
                        content=r["snippet"],
                        title=r["title"]
                    )
                )
        else:
            for r in search_result["search"]:
                metadata = r["metadata"]
                sources.append(
                    SourceMetadata(
                        url=metadata.get("source", ""),
                        content=metadata.get("description" , ''),
                        title=metadata.get("title", " ")
                    )
                )
        for r in search_result["image"]:
            images.append(
                ImageMetadata(
                    url=r["link"],
                    img_url=r["image_url"],
                    title=r["thumbnail"],
                )
            )
        
        return sources, images

web_writer_agent_node = InsightsWriterAgent()


