from typing import Literal, List

from appwrite.client import AppwriteException
from db._appwrite.model_base import AppwriteModelBase
from db._appwrite.fields import AppwriteField
from appwrite.input_file import InputFile
from appwrite import query
from fastapi import UploadFile

class UserProfile(AppwriteModelBase):
    collection_id = "user_profile"
    
    avatar = AppwriteField(size=255, required=False)
    gender: Literal["male", "female"] = AppwriteField(required=False, size=40)
    phone: str = AppwriteField(size=40, required=False)
    address: str = AppwriteField(size=255, required=False)
    city: str = AppwriteField(size=255, required=False)
    country: str = AppwriteField(size=255, required=False)
    # user_id: str = AppwriteField(size=255)
    # user_hash = AppwriteField(type="index", index_attr=["user_id"], index_type="key")

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
        
        profile = await cls.get_or_create(user_id, {'avatar': None})
        avatar = profile.avatar
        if avatar is not None:
            file_id = avatar
            await cls.update_file(avatar, input_file)
            
        else:
            file_id = cls.get_unique_id()
            await cls.create_file(file_id, input_file)
        
        await cls.update(profile.id, {"avatar": file_id}) 

        return file_id



class UserPreferences(AppwriteModelBase):

    collection_id = "user_preference"
    interest: List[str] = AppwriteField(array=True, type="array", default=[])
    price_range: str = AppwriteField(size=255)
    shopping_frequency: str = AppwriteField(size=255)
    preferred_categories: List[str] = AppwriteField(array=True, type="array", default=[])
    notification_preferences: List[str] = AppwriteField(array=True, type="array",default=[])

    # user_id: str = AppwriteField(size=255)
    # user_hash = AppwriteField(type="index", index_attr=["user_id"], index_type="key")