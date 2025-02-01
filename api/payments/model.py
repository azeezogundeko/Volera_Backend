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