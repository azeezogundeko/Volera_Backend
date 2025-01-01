import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("AUTH_SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

SEARCH_ENGINE_URL = str(os.getenv("SEARCH_ENGINE_URL"))

APPWRITE_PROJECT_ID: str = os.getenv("APPWRITE_PROJECT_ID")
APPWRITE_ENDPOINT: str = os.getenv("APPWRITE_ENDPOINT", "https://cloud.appwrite.io/v1")
APPWRITE_DATABASE_ID: str = os.getenv("APPWRITE_DATABASE_ID")
MESSAGE_COLLECTION_ID = "messages"
CHAT_COLLECTION_ID = "chats"
MONGODB_URL = str(os.getenv("MONGODB_URL"))
GOOGLE_SEARCH_ID = str(os.getenv("SEARCH_ENGINE_ID"))
SEARXNG_BASE_URL = str(os.getenv("SEARXNG_BASE_URL"))


class ApiKeyConfig:
    APPWRITE_API_KEY: str = os.getenv("APPWRITE_API_KEY")
    GROQ_API_KEY = str(os.getenv("GROQ_API_KEY"))
    GEMINI_API_KEY = str(os.getenv("GEMINI_API_KEY"))
    GOOGLE_SEARCH_API_KEY = str(os.getenv("GOOGLE_SERP_KEY"))