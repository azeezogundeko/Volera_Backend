from dataclasses import dataclass
from config import ApiKeyConfig
from httpx import AsyncClient
from itertools import cycle


GEMINI_API_KEY_2 = ApiKeyConfig.GEMINI_API_KEY_2
GEMINI_API_KEY = ApiKeyConfig.GEMINI_API_KEY
GEMINI_API_KEY_4 = ApiKeyConfig.GEMINI_API_KEY_4
GEMINI_API_KEY_3 = ApiKeyConfig.GEMINI_API_KEY_3

# Create a cycle iterator for the API keys
_api_key_cycle = cycle([GEMINI_API_KEY, GEMINI_API_KEY_2])
_serp_api_key_cycle = cycle([GEMINI_API_KEY_3, GEMINI_API_KEY_4])

def get_next_gemini_api_key() -> str:
    """
    Returns the next Gemini API key in the rotation.
    This function alternates between the two available API keys.
    
    Returns:
        str: The next API key to use
    """
    return next(_api_key_cycle)

def get_next_serp_api_key() -> str:
    """
    Returns the next Gemini API key in the rotation.
    This function alternates between the two available API keys.
    
    Returns:
        str: The next API key to use
    """
    return next(_serp_api_key_cycle)


@dataclass
class BaseDependencies:
    http_client: AsyncClient 


@dataclass
class GeminiDependencies(BaseDependencies):
    api_key: str = get_next_gemini_api_key()

@dataclass
class ScrapingDependencies(BaseDependencies):
    api_key: str = get_next_serp_api_key()


@dataclass
class GroqDependencies(BaseDependencies):
    api_key: str = ApiKeyConfig.GROQ_API_KEY

@dataclass
class OpenRouterDependencies(BaseDependencies):
    api_key: str = ApiKeyConfig.OPEN_ROUTER_API_KEY

@dataclass
class DeepSeekDependencies(BaseDependencies):
    api_key: str = ApiKeyConfig.DEEPSEEK_API_KEY


def get_dependencies(model_name: str) -> BaseDependencies:
    """
    Get the appropriate dependency class based on the model name.
    The function extracts the base model name from variations (e.g. gemini-pro, gemini-flash both return GeminiDependencies)
    
    Args:
        model_name (str): The name of the model (e.g. "gemini-pro", "groq-mixtral", etc.)
        
    Returns:
        BaseDependencies: The appropriate dependency class for the model
        
    Raises:
        ValueError: If no matching dependency is found for the model
    """
    model_name = model_name.lower()
    
    if "gemini" in model_name:
        return GeminiDependencies
    elif "deepseek" in model_name:
        return DeepSeekDependencies
    else:
        return GeminiDependencies
