import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
# PRODUCTION_MODE = 'true'

PRODUCTION_MODE = os.getenv("PRODUCTION_MODE", "false").lower() == "true"
print(PRODUCTION_MODE)
PRODUCTION_MODE = False
if PRODUCTION_MODE:
    APPWRITE_PROJECT_ID: str = os.getenv("APPWRITE_PROJECT_ID")
    APPWRITE_BUCKET_ID: str = os.getenv("APPWRITE_BUCKET_ID")
    APPWRITE_ENDPOINT: str = os.getenv("APPWRITE_ENDPOINT", "https://cloud.appwrite.io/v1")
    APPWRITE_DATABASE_ID: str = os.getenv("APPWRITE_DATABASE_ID")
    PAYSTACK_SECRET_KEY = str(os.getenv("PAYSTACK_SECRET_KEY"))
    REDIRECT_URI = str(os.getenv("REDIRECT_URI"))
else:
    APPWRITE_PROJECT_ID: str = os.getenv("APPWRITE_PROJECT_ID_TEST")
    APPWRITE_BUCKET_ID: str = os.getenv("APPWRITE_BUCKET_ID_TEST")
    APPWRITE_ENDPOINT: str = os.getenv("APPWRITE_ENDPOINT_TEST", "https://cloud.appwrite.io/v1")
    APPWRITE_DATABASE_ID: str = os.getenv("APPWRITE_DATABASE_ID_TEST")
    PAYSTACK_SECRET_KEY = str(os.getenv("PAYSTACK_SECRET_KEY_TEST"))
    REDIRECT_URI = str(os.getenv("REDIRECT_URI_TEST"))
    
# PRODUCTION_MODE='false'
SECRET_KEY = os.getenv("AUTH_SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")) * 24 * 60

PORT = os.getenv("PORT")
SEARCH_ENGINE_URL = str(os.getenv("SEARCH_ENGINE_URL"))

GOOGLE_CLIENT_ID = str(os.getenv("GOOGLE_CLIENT_ID"))
GOOGLE_CLIENT_SECRET = str(os.getenv("GOOGLE_CLIENT_SECRET"))
REDIRECT_URI = str(os.getenv("REDIRECT_URI"))


MESSAGE_COLLECTION_ID = "messages"
CHAT_COLLECTION_ID = "chats"
MONGODB_URL = str(os.getenv("MONGODB_URL"))
GOOGLE_SEARCH_ID = str(os.getenv("SEARCH_ENGINE_ID"))
SEARXNG_BASE_URL = str(os.getenv("SEARXNG_BASE_URL"))
USER_AGENT= os.getenv("USER_AGENT")
ID_SECRET_KEY = os.getenv("ID_SECRET_KEY")

KONGA_API_KEY = str(os.getenv("KONGA_API_KEY"))
KONGA_ID = str(os.getenv("KONGA_ID"))



SENTRY_API_KEY = str(os.getenv("SENTRY_API_KEY"))

DB_DIR = Path("data/db")
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "cache"

URL_CACHE_DIR = Path("data/url_cache")
URL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
SEARCH_CACHE_DIR = Path("data/search_cache")
SEARCH_CACHE_DIR.mkdir(parents=True, exist_ok=True)
MEMORY_CACHE_DIR = Path("data/memory_cache")
MEMORY_CACHE_DIR.mkdir(parents=True, exist_ok=True)

USER_AGENT= str(os.getenv("USER_AGENT"))

class ApiKeyConfig:
    APPWRITE_API_KEY: str = os.getenv("APPWRITE_API_KEY") if PRODUCTION_MODE else os.getenv("APPWRITE_API_KEY_TEST")
    GROQ_API_KEY = str(os.getenv("GROQ_API_KEY"))
    GEMINI_API_KEY_2 = str(os.getenv("GEMINI_API_KEY_2"))
    GEMINI_API_KEY_3 = str(os.getenv("GEMINI_API_KEY_3"))
    GEMINI_API_KEY_4 = str(os.getenv("GEMINI_API_KEY_4"))
    GEMINI_API_KEY = str(os.getenv("GEMINI_API_KEY"))
    GOOGLE_SEARCH_API_KEY = str(os.getenv("GOOGLE_SERP_KEY"))
    OPEN_ROUTER_API_KEY = str(os.getenv("OPEN_ROUTER_API_KEY"))
    DEEPSEEK_API_KEY = str(os.getenv("DEEPSEEK_API_KEY"))

# Flare Bypasser Configuration
FLARE_BYPASSER_URL = os.getenv("FLARE_BYPASSER_URL", "http://flare-bypasser:20080") if PRODUCTION_MODE else None 

proxy_host = os.getenv('PROXY_HOST')
proxy_port = os.getenv('PROXY_PORT')
proxy_auth = os.getenv('PROXY_AUTH')
proxy_url = f"http://{proxy_auth}@{proxy_host}:{proxy_port}"
