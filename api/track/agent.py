from pydantic import BaseModel
from pydantic_ai import Agent
from dataclasses import dataclass
from httpx import AsyncClient
from config import ApiKeyConfig


class PriceHistory(BaseModel):
    price: float
    discount: float


@dataclass
class Dependencies:
    api_key: ApiKeyConfig.GEMINI_API_KEY
    http_client: AsyncClient 


system_prompt = """


"""

price_extrator = Agent(
    model="gemini-1.5-flash",
    result_type=PriceHistory,
    deps_type=Dependencies,
    name="Price Agent",
    system_prompt=system_prompt,

)

