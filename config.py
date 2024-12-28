import os
from dotenv import load_dotenv

load_dotenv()

SEARCH_ENGINE_URL = str(os.getenv("SEARCH_ENGINE_URL"))

APPWRITE_PROJECT_ID: str = os.getenv("APPWRITE_PROJECT_ID")
APPWRITE_ENDPOINT: str = os.getenv("APPWRITE_ENDPOINT", "https://cloud.appwrite.io/v1")
APPWRITE_DATABASE_ID: str = os.getenv("APPWRITE_DATABASE_ID")
MESSAGE_COLLECTION_ID = "messages"
CHAT_COLLECTION_ID = "chats"


class ApiKeyConfig:
    APPWRITE_API_KEY: str = os.getenv("APPWRITE_API_KEY")
    GROQ_API_KEY = str(os.getenv("GROQ_API_KEY"))
    GEMINI_API_KEY = str(os.getenv("GEMINI_API_KEY"))