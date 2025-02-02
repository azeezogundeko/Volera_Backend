from typing import Literal, List
from db._appwrite.model_base import AppwriteModelBase
from db._appwrite.fields import AppwriteField
from appwrite.input_file import InputFile
from appwrite import query
from fastapi import UploadFile

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

    @classmethod
    async def upload_profile_image(cls, user_id: str, file: UploadFile) -> str:
        """
        Upload a profile image for a user.
        
        :param user_id: The ID of the user
        :param file: The uploaded file
        :return: The ID of the uploaded file
        """
        # Read file contents
        file_bytes = await file.read()
        
        # Create Appwrite InputFile
        input_file = InputFile.from_bytes(
            file_bytes,
            file.filename
        )
        
        # Find existing profile
        existing_profile = await cls.list(
            queries=[query.Query.equal("user_id", user_id)], 
            limit=1
        )
        
        # If profile exists, update the file
        if existing_profile["documents"]:
            profile_doc = existing_profile["documents"][0]
            file_id = await cls.update_file(profile_doc.id, input_file)
            return file_id
        
        # If no profile exists, create a new one with the file
        file_id = await cls.create_file(user_id, input_file)
        return file_id



class UserPreferences(AppwriteModelBase):

    collection_id = "user_preference"
    interest: List[str] = AppwriteField(array=True, type="array", default=[])
    price_range: str = AppwriteField(size=255)
    shopping_frequency: str = AppwriteField(size=255)
    preferred_categories: List[str] = AppwriteField(array=True, type="array", default=[])
    notification_preferences: List[str] = AppwriteField(array=True, type="array",default=[])

    user_id: str = AppwriteField(size=255)
    user_hash = AppwriteField(type="index", index_attr=["user_id"], index_type="key")