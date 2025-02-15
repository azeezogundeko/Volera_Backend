from dataclasses import dataclass
from config import ApiKeyConfig
from httpx import AsyncClient
from itertools import cycle


GEMINI_API_KEY_2 = ApiKeyConfig.GEMINI_API_KEY_2
GEMINI_API_KEY = ApiKeyConfig.GEMINI_API_KEY

# Create a cycle iterator for the API keys
_api_key_cycle = cycle([GEMINI_API_KEY, GEMINI_API_KEY_2])

def get_next_gemini_api_key() -> str:
    """
    Returns the next Gemini API key in the rotation.
    This function alternates between the two available API keys.
    
    Returns:
        str: The next API key to use
    """
    return next(_api_key_cycle)


@dataclass
class BaseDependencies:
    http_client: AsyncClient 


@dataclass
class GeminiDependencies(BaseDependencies):
    api_key: str = get_next_gemini_api_key()


@dataclass
class GroqDependencies(BaseDependencies):
    api_key: str = ApiKeyConfig.GROQ_API_KEY
