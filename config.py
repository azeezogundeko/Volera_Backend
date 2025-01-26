import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

SECRET_KEY = os.getenv("AUTH_SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")) * 24 * 60

PORT = os.getenv("PORT")
SEARCH_ENGINE_URL = str(os.getenv("SEARCH_ENGINE_URL"))

APPWRITE_PROJECT_ID: str = os.getenv("APPWRITE_PROJECT_ID")
APPWRITE_BUCKET_ID: str = os.getenv("APPWRITE_BUCKET_ID")
APPWRITE_ENDPOINT: str = os.getenv("APPWRITE_ENDPOINT", "https://cloud.appwrite.io/v1")
APPWRITE_DATABASE_ID: str = os.getenv("APPWRITE_DATABASE_ID")
MESSAGE_COLLECTION_ID = "messages"
CHAT_COLLECTION_ID = "chats"
MONGODB_URL = str(os.getenv("MONGODB_URL"))
GOOGLE_SEARCH_ID = str(os.getenv("SEARCH_ENGINE_ID"))
SEARXNG_BASE_URL = str(os.getenv("SEARXNG_BASE_URL"))
USER_AGENT= os.getenv("USER_AGENT")
ID_SECRET_KEY = os.getenv("ID_SECRET_KEY")

KONGA_API_KEY = str(os.getenv("KONGA_API_KEY"))
KONGA_ID = str(os.getenv("KONGA_ID"))

DB_DIR = Path("data/db")
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "cache"

URL_CACHE_DIR = Path("data/url_cache")
URL_CACHE_DIR.mkdir(parents=True, exist_ok=True)

class ApiKeyConfig:
    APPWRITE_API_KEY: str = os.getenv("APPWRITE_API_KEY")
    GROQ_API_KEY = str(os.getenv("GROQ_API_KEY"))
    GEMINI_API_KEY = str(os.getenv("GEMINI_API_KEY"))
    GOOGLE_SEARCH_API_KEY = str(os.getenv("GOOGLE_SERP_KEY")) 