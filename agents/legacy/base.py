from ..config import agent_manager
from schema import MetaAgentSchema, GroqDependencies

from pydantic_ai import Agent


def create_meta_agent(prompt: str)-> Agent:
    return Agent(
            name=agent_manager.meta_agent,
            retries=3,
            system_prompt=prompt,
            model="groq:llama3-groq-70b-8192-tool-use-preview",
            deps_type=GroqDependencies,
            result_type=MetaAgentSchema,
        )

policy_agent = Agent(
            name=agent_manager.meta_agent,
            retries=3,
            system_prompt="",
            model=model,
            deps_type=...,
        )

writer_agent = Agent(
            name=agent_manager.meta_agent,
            retries=3,
            system_prompt="",
            model=model,
            deps_type=...,
        )

comparison_agent = Agent(
            name=agent_manager.meta_agent,
            retries=3,
            system_prompt="",
            model=model,
            deps_type=...,
        )

reviewer_agent = Agent(
            name=agent_manager.meta_agent,
            retries=3,
            system_prompt="",
            model=model,
            deps_type=...,
        )

shop_agent = Agent(
            name=agent_manager.meta_agent,
            retries=3,
            system_prompt="",
            model=model,
            deps_type=...,
        )

memory_agent = Agent(
            name=agent_manager.meta_agent,
            retries=3,
            system_prompt="",
            model=model,
            deps_type=...,
        )

search_agent = Agent(
            name=agent_manager.meta_agent,
            retries=3,
            system_prompt="",
            model=model,
            deps_type=...,
        )

