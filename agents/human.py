from typing import Literal

import prompts

from .config import agent_manager
from utils.logging import logger
from schema import extract_agent_results
from .legacy.base import create_human_agent
from .state import State
from utils.helper_state import get_current_request

from langgraph.types import Command
from pydantic_ai.result import RunResult

def get_prompt():
    prompt = f"""
        ### Role and Goal
        You are a highly skilled, professional, and empathetic assistant. Your task is to transform the agent's instructions 
        into a concise, engaging, and human-friendly response for the user. The response should be:

        - Polite and approachable.
        - Helpful and actionable.
        - Clear, with simplified explanations that avoid complex jargon.

        ### Key Instructions
        - **Simplify complex terms** without losing their meaning.
        - **Use friendly language** to maintain a conversational tone.
        - **Address the user directly** to create a personalized experience.
        - Format your response **professionally in Markdown** for the best user experience.

        ### Instructions for Response
        Use headings, bullet points, or numbered lists when appropriate, and ensure the structure is clean and readable. 
        Provide specific and actionable guidance that aligns with the agent's instructions.

        ### Agent's Instructions
        <>
        
        """
    return prompt


# Secure wrapper to handle agent responses safely
@extract_agent_results(agent_manager.human_node)
async def human_agent(state: State, config={}) -> RunResult:
    try:
        current_request = get_current_request(state)
        if not current_request or "message" not in current_request or "content" not in current_request["message"]:
            raise ValueError("Invalid or missing 'content' in current request.")
        
        if state["previous_node"] == agent_manager.meta_agent:
            result = state["agent_results"][agent_manager.meta_agent]
            result = result["content"]["result"].instructions

            
        elif state["previous_node"] == agent_manager.policy_agent:
            result = state["agent_results"][agent_manager.policy_agent]
            result = result.__dict__

        if not isinstance(result, list):
            result = [str(result)]
    
        # Prepare prompt with extracted instructions
        prompts = get_prompt() + "\n" + "\n".join(result)

        llm = create_human_agent(prompts)
        response = await llm.run(user_prompt=prompts)
        return response

    except Exception as e:
        logger.error("Failed to execute search agent operation", exc_info=True)
        raise RuntimeError(f"Failed to execute search agent: {e}")


async def human_agent_node(state: State) -> Command[Literal[agent_manager.end]]:
    try:
        r = await human_agent(state)
        print(r.data)
        logger.info("Processed agent results and transitioning to the next node.")
        final = state["agent_results"][agent_manager.human_node]["content"]
        state["final_result"] = final["result"].content
        return Command(goto=agent_manager.end, update=state)

    except Exception as e:
        logger.error("Unexpected error during search agent node processing.", exc_info=True)
        raise RuntimeError("Unexpected error occurred.") from e
