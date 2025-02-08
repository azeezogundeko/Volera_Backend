from .model_base import AppwriteModelBase #, CollectionMetadata

from api.track.model import TrackedItem, PriceHistory
from api.chat.model import Chat, Message, File, SavedChat, MessageImage
from api.product.model import Product, WishList
from api.auth.model import UserProfile, UserPreferences
from api.admin.model import Contact
from api.admin.model import DailyLog, MonthlyLog, AppLog
# from agents.legacy.llm import LLMCall
from api.payments.model import Subscription, SubscriptionLog, DailyUsage

from .fields import AppwriteField

class WaitList(AppwriteModelBase):
    collection_id= "waitlist"
    email: str = AppwriteField()

AppwriteModelBase.register_model(TrackedItem)
AppwriteModelBase.register_model(Product)
AppwriteModelBase.register_model(WaitList)
AppwriteModelBase.register_model(Subscription)
AppwriteModelBase.register_model(SubscriptionLog)
AppwriteModelBase.register_model(DailyUsage)
AppwriteModelBase.register_model(WishList)
AppwriteModelBase.register_model(MessageImage)
AppwriteModelBase.register_model(PriceHistory)
AppwriteModelBase.register_model(Chat)
AppwriteModelBase.register_model(Message)
AppwriteModelBase.register_model(File)
AppwriteModelBase.register_model(UserPreferences)
AppwriteModelBase.register_model(UserProfile)
AppwriteModelBase.register_model(SavedChat)
AppwriteModelBase.register_model(Contact)
AppwriteModelBase.register_model(DailyLog)
AppwriteModelBase.register_model(MonthlyLog)
AppwriteModelBase.register_model(AppLog)
# AppwriteModelBase.register_model(Stores)


async def prepare_database():
    await AppwriteModelBase.create_all_collections()