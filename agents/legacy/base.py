from ..config import agent_manager
from prompts import (
    search_agent_prompt, 
    policy_assistant_prompt, 
    planner_agent_prompt
    )
from schema.dataclass.dependencies import GroqDependencies, GeminiDependencies
from schema.validations.agents_schemas import( 
    PlannerAgentSchema, 
    SearchAgentSchema, 
    ComparisonSchema,
    InsightsSchema,
    ReviewerSchema,
    PolicySchema,
    HumanSchema,
    FeedbackResponseSchema,
    )

from pydantic_ai import Agent


def create_meta_agent()-> Agent:
    return Agent(
            name=agent_manager.meta_agent,
            retries=3,
            system_prompt=planner_agent_prompt,
            model="gemini-1.5-flash",
            deps_type=GeminiDependencies,
            result_type=PlannerAgentSchema,
        )
def create_planner_agent()-> Agent:
    return Agent(
            name=agent_manager.meta_agent,
            retries=3,
            system_prompt=planner_agent_prompt,
            model="gemini-1.5-flash",
            deps_type=GeminiDependencies,
            result_type=PlannerAgentSchema,
        )
def create_copilot_agent(prompt)-> Agent:
    return Agent(
            name=agent_manager.copilot_mode,
            retries=3,
            system_prompt=prompt,
            model="gemini-1.5-flash",
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
def create_writer_agent(prompt)-> Agent:
    return Agent(
        name=agent_manager.writer_agent,
        retries=3,
        system_prompt=prompt,
        model="gemini-1.5-flash",
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

