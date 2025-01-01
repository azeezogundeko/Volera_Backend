from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from ..base import AsyncAppWriteClient

from appwrite.query import Query

class UserService:
    def __init__(self):
        self.client = AsyncAppWriteClient()
        self.collection_id = "users"

    
    async def get(self, email: str):
        self.client.get_document(
            self.collection_id
        )




class UserProfileService:
    def __init__(self):
        self.client = AsyncAppWriteClient()
        self.collection_id = "user_profiles"

    async def create_profile(self, user_id: str, full_name: str, country: str, profile_picture_url: Optional[str] = None) -> Dict[str, Any]:
        document_data = {
            "user_id": user_id,
            "full_name": full_name,
            "profile_picture_url": profile_picture_url,
            "country": country,
            "date_registered": datetime.now(timezone.utc).isoformat(),
        }
        return await self.client.create_document(self.collection_id, document_data)

    async def get_profile(self, profile_id: str) -> Dict[str, Any]:
        return await self.client.get_document(self.collection_id, profile_id)

    async def update_profile(self, profile_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        return await self.client.update_document(self.collection_id, profile_id, updates)


class ShoppingPreferencesService:
    def __init__(self):
        self.client = AsyncAppWriteClient()
        self.collection_id = "shopping_preferences"

    async def create_preferences(self, user_id: str, favorite_categories: List[str], price_range: Dict[str, float]) -> Dict[str, Any]:
        document_data = {
            "user_id": user_id,
            "favorite_categories": favorite_categories,
            "price_range": price_range,
        }
        return await self.client.create_document(self.collection_id, document_data)

    async def get_preferences(self, user_id: str) -> Dict[str, Any]:
        return await self.client.get_document(self.collection_id, user_id)

    async def update_preferences(self, preferences_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        return await self.client.update_document(self.collection_id, preferences_id, updates)


class UserActivityService:
    def __init__(self):
        self.client = AsyncAppWriteClient()
        self.collection_id = "user_activity"

    async def log_activity(self, user_id: str, activity_data: Dict[str, Any]) -> Dict[str, Any]:
        document_data = {"user_id": user_id, **activity_data}
        return await self.client.create_document(self.collection_id, document_data)

    async def get_user_activity(self, user_id: str) -> List[Dict[str, Any]]:
        return await self.client.list_documents(self.collection_id, queries=[f"user_id={user_id}"])


class CommunicationPreferencesService:
    def __init__(self):
        self.client = AsyncAppWriteClient()
        self.collection_id = "communication_preferences"

    async def set_preferences(self, user_id: str, preferences: Dict[str, bool]) -> Dict[str, Any]:
        document_data = {
            "user_id": user_id,
            "preferences": preferences,
        }
        return await self.client.create_document(self.collection_id, document_data)

    async def get_preferences(self, user_id: str) -> Dict[str, Any]:
        return await self.client.get_document(self.collection_id, user_id)


class TechnicalMetadataService:
    def __init__(self):
        self.client = AsyncAppWriteClient()
        self.collection_id = "technical_metadata"

    async def log_metadata(self, user_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        document_data = {"user_id": user_id, **metadata}
        return await self.client.create_document(self.collection_id, document_data)


class SecurityComplianceService:
    def __init__(self):
        self.client = AsyncAppWriteClient()
        self.collection_id = "security_compliance"

    async def set_security_settings(self, user_id: str, settings: Dict[str, Any]) -> Dict[str, Any]:
        document_data = {
            "user_id": user_id,
            **settings,
        }
        return await self.client.create_document(self.collection_id, document_data)

    async def get_security_settings(self, user_id: str) -> Dict[str, Any]:
        return await self.client.get_document(self.collection_id, user_id)
