from ..planner_agent import PlannerAgent
from .prompts.planner_prompt import planner_agent_prompt


class ComparisonPlannerAgent(PlannerAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(system_prompt=planner_agent_prompt,
            *args, **kwargs
            )
