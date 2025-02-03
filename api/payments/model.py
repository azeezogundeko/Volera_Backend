import pytz
import hashlib
from datetime import datetime

from api.auth.schema import UserIn
from db._appwrite.fields import AppwriteField
from db._appwrite.model_base import AppwriteModelBase

from appwrite.exception import AppwriteException


class Subscription(AppwriteModelBase):
    collection_id = 'subscription'
    
    user_id = AppwriteField()
    plan = AppwriteField()
    amount = AppwriteField(type="float")
    channel = AppwriteField(required=False)
    currency = AppwriteField()
    transaction_id = AppwriteField()


class SubscriptionLog(AppwriteModelBase):
    collection_id = 'error_log'


    user_id = AppwriteField()
    error = AppwriteField()
    is_fixed = AppwriteField(type="bool", default=False)

    @classmethod
    async def create(cls, user_id, error):
        await super().create(cls.get_unique_id(), {
            "user_id": user_id,
            "error": error
        })
        # send an email to support @solvebyte.com

class DailyUsage(AppwriteModelBase):
    collection_id = "daily_usage"
    
    # Define model attributes (for schema and local validation if needed)
    user_id: str = AppwriteField()
    day: str = AppwriteField() # store as YYYY-MM-DD string
    total_credits: int = AppwriteField(type="int", default=0)

    @classmethod
    async def update_usage(cls, user_id: str, timestamp: datetime, delta: int, user_timezone: str) -> None:
        """
        Update daily usage for a given user at the provided timestamp.
        
        :param user_id: The user’s ID.
        :param timestamp: The UTC timestamp of the transaction.
        :param delta: The amount to add (can be negative).
        :param user_timezone: The user's timezone (e.g. "America/New_York").
        """
        # Convert the provided timestamp to the user's local timezone.
        if user_timezone is None:
            user_timezone = 'UTC'
        tz = pytz.timezone(user_timezone)
        local_time = timestamp.astimezone(tz)
        short_user_id = hashlib.md5(user_id.encode()).hexdigest()[:8]
        day_str = local_time.strftime("%Y-%m-%d")
        
        # Build a unique document id for daily usage (e.g. "userID_2024-01-15")
        document_id = f"{short_user_id}_{day_str}"
        
        try:
            # Try to read the existing document.
            daily_doc = await cls.read(document_id)
            new_total = daily_doc.total_credits + delta
            await cls.update(document_id, {"total_credits": new_total})
        except AppwriteException:
            # Document does not exist; create a new one.
            data = {
                "user_id": user_id,
                "day": day_str,
                "total_credits": delta
            }
            await cls.create(document_id, data)


class MonthlyUsage(AppwriteModelBase):
    collection_id = "monthly_usage"
    
    # Define model attributes.
    user_id: str = AppwriteField()
    month: str = AppwriteField() # store as YYYY-MM (e.g. 2024-01)
    total_credits: int = AppwriteField(type="int", default=0)

    @classmethod
    async def update_usage(cls, user_id: str, timestamp: datetime, delta: int, user_timezone: str) -> None:
        """
        Update monthly usage for a given user.
        
        :param user_id: The user's ID.
        :param timestamp: The UTC timestamp of the transaction.
        :param delta: The amount to add (can be negative).
        :param user_timezone: The user's timezone.
        """
        tz = pytz.timezone(user_timezone)
        local_time = timestamp.astimezone(tz)
        month_str = local_time.strftime("%Y-%m")
        
        document_id = f"{user_id}_{month_str}"
        
        try:
            monthly_doc = await cls.read(document_id)
            new_total = monthly_doc.total_credits + delta
            await cls.update(document_id, {"total_credits": new_total})
        except AppwriteException:
            data = {
                "user_id": user_id,
                "month": month_str,
                "total_credits": delta
            }
            await cls.create(document_id, data)

