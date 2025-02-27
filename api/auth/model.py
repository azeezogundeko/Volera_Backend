from typing import Literal, List
from asyncio import to_thread
from datetime import datetime

from appwrite.client import AppwriteException
from db._appwrite.model_base import AppwriteModelBase
from db._appwrite.fields import AppwriteField
from db import user_db

from appwrite.input_file import InputFile
from appwrite.query import Query
from fastapi import UploadFile
from utils.logging import logger


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
    price_range: str = AppwriteField(size=255, required=False)
    shopping_frequency: str = AppwriteField(size=255, required=False)
    preferred_categories: List[str] = AppwriteField(array=True, type="array", default=[])
    notification_preferences: List[str] = AppwriteField(array=True, type="array",default=[])

    # user_id: str = AppwriteField(size=255)
    # user_hash = AppwriteField(type="index", index_attr=["user_id"], index_type="key")


class Referral(AppwriteModelBase):
    """
    A model to store referral information for a user.
    """
    collection_id = "referral"

    user_id: str = AppwriteField(size=255)
    referral_code: str = AppwriteField(size=255)
    referral_count: int = AppwriteField(default=0, type="int")
    referral_limit: int = AppwriteField(default=100, type="int")
    referral_status: Literal["active", "inactive"] = AppwriteField(default="active")
    referred_by: str = AppwriteField(size=255, required=False)


    @classmethod
    async def create_referral(cls, user_id: str, referral_code: str):
        """
        Create a new referral for a user.
        """
        referral = await cls.create(cls.get_unique_id(), {"referral_code": referral_code, "user_id": user_id})
        return referral
    
    @classmethod
    async def refer_user(cls, user_to_refer_id: str, referral_code: str):
        """
        Refer a user to the platform.
        Returns None if:
        - Referral code doesn't exist
        - Referral is inactive
        - Referral limit has been reached
        Otherwise returns the updated referral object
        """
        try:
            # Get the original referrer's info
            original_user = await cls.get_referral_by_code(referral_code)
            if original_user is None:
                return None
            
            user_id = original_user.user_id

            # Get referral object
            referral = await cls.get_referral_by_user_id(user_id)
            if referral is None:
                return None

            # Check referral status
            if referral.referral_status == "inactive":
                return None
            
            # Check referral limit
            if referral.referral_count >= referral.referral_limit:
                # Update status to inactive
                await cls.update(referral.id, {"referral_status": "inactive"})
                return None

            # Increment referral count and update referred_by
            new_count = referral.referral_count + 1
            await cls.update(referral.id, {
                "referral_count": new_count,
                "referred_by": original_user.user_id
            })

            # Update credits for both users
            await UserCredits.update_balance(user_to_refer_id, 250, "referral_bonus_recipient")
            await UserCredits.update_balance(user_id, 500, "referral_bonus_referrer")

            # Get and return updated referral object
            return await cls.get_referral_by_user_id(user_id)
            
        except Exception as e:
            logger.error(f"Error in refer_user: {str(e)}")
            return None
    
    @classmethod
    async def update_referral(cls, user_id: str, referral_code: str):
        """
        Update a referral for a user.
        Returns None if the referral doesn't exist.
        """
        try:
            # First get the referral to ensure it exists
            referral = await cls.get_referral_by_user_id(user_id)
            if referral is None:
                return None
                
            # Update the referral code
            updated = await cls.update(referral.id, {"referral_code": referral_code})
            return updated
        except Exception as e:
            logger.error(f"Error updating referral: {str(e)}")
            return None
    
    @classmethod
    async def get_referral_by_code(cls, referral_code: str):
        """
        Get a referral by its code.
        """
        queries = [Query.equal("referral_code", referral_code)]  # Pass as a list
        referral = await cls.list(queries)
        if referral["total"] == 0:
            return None
        return referral["documents"][0]
    
    @classmethod
    async def get_referral_by_user_id(cls, user_id: str):
        """
        Get a referral by its user ID.
        """
        queries = [Query.equal("user_id", user_id)]  # Pass as a list
        referral = await cls.list(queries)
        if referral["total"] == 0:
            return None
        return referral["documents"][0]

class UserCredits(AppwriteModelBase):
    collection_id = "user_credits"
    
    balance: int = AppwriteField(type="int", default=0)
    last_transaction: str = AppwriteField(size=255)  # Track what changed the balance

    @classmethod
    async def recreate_collection(cls) -> None:
        """Delete and recreate the UserCredits collection."""
        try:
            # Delete the collection
            await cls.client.database.delete_collection(
                database_id=cls.client.database_id,
                collection_id=cls.collection_id
            )
            logger.info(f"Deleted collection {cls.collection_id}")
        except Exception as e:
            logger.warning(f"Error deleting collection {cls.collection_id}: {str(e)}")

        # Recreate the collection
        await cls.create_collection("UserCredits")
        logger.info(f"Recreated collection {cls.collection_id}")

    @classmethod
    async def get_or_create(cls, user_id: str) -> "UserCredits":
        """Get or create a user's credit record."""
        try:
            try:
                credits = await cls.read(user_id)
            except AppwriteException:
                # now = datetime.now().isoformat()
                credits = await cls.create(user_id, {
                    "balance": 500,
                    "last_transaction": "initial_credit"
                })
            return credits
        except Exception as e:
            logger.error(f"Error in get_or_create credits for user {user_id}: {str(e)}")
            raise

    @classmethod
    async def update_balance(cls, user_id: str, delta: int, transaction_type: str = "unknown") -> tuple[int, bool]:
        """
        Update user's credit balance atomically.
        
        Args:
            user_id: The user's ID
            delta: Amount to add (positive) or subtract (negative)
            transaction_type: Type of transaction for logging
            
        Returns:
            tuple[new_balance, success]
        """
        try:
            # Get current credit record
            credit_record = await cls.get_or_create(user_id)
            current_balance = credit_record.balance
            
            # Calculate new balance
            new_balance = current_balance + delta
            
            if new_balance < 0:
                logger.warning(f"Attempted negative balance for user {user_id}: current={current_balance}, delta={delta}")
                return current_balance, False
            
            now = datetime.now().isoformat()
            
            # Update with transaction info
            await cls.update(user_id, {
                "balance": new_balance,
                "last_transaction": f"{transaction_type}:{delta}"
            })
            
            logger.info(f"Credit update for user {user_id}: {current_balance} -> {new_balance} ({delta}) via {transaction_type}")
            return new_balance, True
            
        except Exception as e:
            logger.error(f"Error updating credits for user {user_id}: {str(e)}")
            raise

    @classmethod
    async def get_balance(cls, user_id: str) -> int:
        """Get current credit balance for a user."""
        try:
            credit_record = await cls.get_or_create(user_id)
            return credit_record.balance
        except Exception as e:
            logger.error(f"Error getting credit balance for user {user_id}: {str(e)}")
            raise
