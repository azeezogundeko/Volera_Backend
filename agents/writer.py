from typing import Literal

from fastapi import WebSocket
from .state import State
from .config import agent_manager
from .tools.markdown import convert_to_markdown
from schema import extract_agent_results, ReviewerSchema
from prompts import writer_agent_prompt
from utils.logging import logger
from utils.websocket import ImageMetadata, SourceMetadata

from .legacy.base import BaseAgent
from schema import extract_agent_results
from schema.dataclass.dependencies import GeminiDependencies
from utils.exceptions import AgentProcessingError

from langgraph.types import Command
from pydantic_ai.result import RunResult


class WriterAgent(BaseAgent):
    def __init__(
        self, 
        timeout=10,
        model = "gemini-2.0-flash-exp",
        deps_type = GeminiDependencies,
        result_type = ReviewerSchema,
        system_prompt = writer_agent_prompt,
        name: str = agent_manager.writer_agent, 
    
    ):
        super().__init__(
            name=name,
            retries=3,
            model=model,
            timeout=timeout,
            deps_type=deps_type,
            result_type=result_type,
            system_prompt=system_prompt,
        )


    # Secure wrapper to handle agent responses safely
    @extract_agent_results(agent_manager.writer_agent)
    async def run(self,state: State) -> RunResult:
        search_result = state["agent_results"][agent_manager.search_tool]
        instructions = state["agent_results"][agent_manager.planner_agent]["content"]["writer_instructions"]
        
        instructions = str(instructions)
        past_conversations = state["message_history"]
        results = [r["content"] for r in search_result]

        prompt = {
                "instructions": instructions,
                "search_results": results,
        }
        # ws = state["ws"]
        # await ws.send_json()
        # we for started compiling
        response = await self.llm.run(str(prompt), message_history=past_conversations)
        return response

    async def __call__(self, state: State, config={}) -> Command[Literal[agent_manager.end]]:
        try:
            response = await self.run(state)
            content = convert_to_markdown(response.data.content)
            ws_id: WebSocket = state["ws_id"]
            search_results = state["agent_results"][agent_manager.search_tool]
            
            images = []
            sources = []
            for r in search_results:
                images.append(
                    ImageMetadata(
                        url=r["metadata"].get("product_url", ""),
                        img_url=r["metadata"].get("image_url", ""),
                        title=r["metadata"].get("title", ""),
                        # favicon=r["metadata"].get("image_url", ""),
                    )
                )
                sources.append(
                    SourceMetadata(
                        url=r["metadata"].get("product_url", ""),
                        content=r["content"],
                        title=r["metadata"].get("title", ""),
                    )
                )
            
            # Send sources with comprehensive data
            # send compiling message 


            await self.websocket_manager.send_sources(ws_id, sources)
            await self.websocket_manager.send_json(ws_id, {"type":"message","content":content})
            await self.websocket_manager.send_json(ws_id, {"type":"messageEnd","content":content})
            await self.websocket_manager.send_images(ws_id, images)
            state["ai_response"] = content
            state["next_node"] = agent_manager.followup
            state["previous_node"] = agent_manager.writer_agent

            # Check if we should end the conversation or continue
            await self.evaluate_chat_limit(state)
            logger.info("Continuing conversation for follow-up questions")
            return Command(goto=agent_manager.human_node, update=state)

        except Exception as e:
            logger.error("Unexpected error during search agent node processing.", str(e))
            





writer_agent_node = WriterAgent()
