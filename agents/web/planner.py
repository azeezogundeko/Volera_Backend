from ..planner_agent import PlannerAgent
from ..tools.search_tool import search_internet_tool
from .prompts.planner_prompts import web_planner_agent_prompt
from .schema import WebPlannerAgentSchema


class WebPlannerAgent(PlannerAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(
            system_prompt=web_planner_agent_prompt,
            result_type=WebPlannerAgentSchema,
            *args, **kwargs
            )
    
    async def search(self, result: WebPlannerAgentSchema):
        return await search_internet_tool(
            search_query=result.search_query,
            description=result.description,
            n_k=result.n_k,
            mode="fast",
            type="web"
        )
