import os
from dotenv import load_dotenv

load_dotenv()

SEARCH_ENGINE_URL = str(os.getenv("SEARCH_ENGINE_URL"))

class ApiKeyConfig:
    GROQ_API_KEY = str(os.getenv("GROQ_API_KEY"))
    GEMINI_API_KEY = str(os.getenv("GEMINI_API_KEY"))