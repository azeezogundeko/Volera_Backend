from typing import Literal, List
from db._appwrite.model_base import AppwriteModelBase
from db._appwrite.fields import AppwriteField

class UserProfile(AppwriteModelBase):
    collection_id = "user_profile"
    
    avatar = AppwriteField(size=255, required=False)
    gender: Literal["male", "female"] = AppwriteField(required=True, size=40)
    phone: str = AppwriteField(size=40)
    address: str = AppwriteField(size=255)
    city: str = AppwriteField(size=255)
    country: str = AppwriteField(size=255)
    user_id: str = AppwriteField(size=255)
    user_hash = AppwriteField(type="index", index_attr=["user_id"], index_type="key")



class UserPreferences(AppwriteModelBase):

    collection_id = "user_preference"
    interest: List[str] = AppwriteField(array=True, type="array", default=[])
    price_range: str = AppwriteField(size=255)
    shopping_frequency: str = AppwriteField(size=255)
    preferred_categories: List[str] = AppwriteField(array=True, type="array", default=[])
    notification_preferences: List[str] = AppwriteField(array=True, type="array",default=[])

    user_id: str = AppwriteField(size=255)
    user_hash = AppwriteField(type="index", index_attr=["user_id"], index_type="key")