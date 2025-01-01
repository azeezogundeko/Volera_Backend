from ._appwrite.base import async_appwrite
from ._appwrite.chat import prepare_database
from .cache.manager import cache_manager
from .cache.decourator import cached, invalidate_cache
from .sqlite.appwrite import start_session_sync_task, push_sessions_to_appwrite
from appwrite.services.users import Users

user_db = Users(async_appwrite.client)
USER_COLLECTION_ID = "users"
USER_PROFILE_COLLECTION_ID = "users"
USER_ACTIVITY_COLLECTION_ID = "users_activity"
USER_PREFERENCES_COLLECTION_ID = "users"
USER_COLLECTION_ID = "users"

__all__ = [
    "user_db",
    "AsyncUsersWrapper",
    "async_appwrite",
    "prepare_database",
    "cache_manager",
    "cached",
    "invalidate_cache",
    "start_session_sync_task",
    "push_sessions_to_appwrite"
]