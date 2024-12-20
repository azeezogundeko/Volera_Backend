from dataclasses import dataclass
from config import ApiKeyConfig
from httpx import AsyncClient


@dataclass
class BaseDependencies:
    http_client: AsyncClient 


@dataclass
class GeminiDependencies(BaseDependencies):
    api_key: str = ApiKeyConfig.GEMINI_API_KEY


@dataclass
class GroqDependencies(BaseDependencies):
    api_key: str = ApiKeyConfig.GROQ_API_KEY
