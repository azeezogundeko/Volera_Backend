from locale import currency
from db._appwrite.fields import AppwriteField
from db._appwrite.model_base import AppwriteModelBase


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