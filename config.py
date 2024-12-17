import os
from dotenv import load_dotenv

load_dotenv()

class ApiKeyConfig:
    GROQ_API_KEY = str(os.getenv("GROQ_API_KEY"))
    GEMINI_API_KEY = str(os.getenv("GEMINI_API_KEY"))