from .model_base import AppwriteModelBase #, CollectionMetadata

from api.track.model import TrackedItem, PriceHistory
from api.chat.model import Chat, Message, File, SavedChat, MessageImage
from api.product.model import Product, WishList
from api.auth.model import UserProfile, UserPreferences


AppwriteModelBase.register_model(TrackedItem)
AppwriteModelBase.register_model(Product)
AppwriteModelBase.register_model(WishList)
AppwriteModelBase.register_model(MessageImage)
AppwriteModelBase.register_model(PriceHistory)
AppwriteModelBase.register_model(Chat)
AppwriteModelBase.register_model(Message)
AppwriteModelBase.register_model(File)
AppwriteModelBase.register_model(UserPreferences)
AppwriteModelBase.register_model(UserProfile)
AppwriteModelBase.register_model(SavedChat)
# AppwriteModelBase.register_model(Specification)
# AppwriteModelBase.register_model(Stores)


async def prepare_database():
    await AppwriteModelBase.create_all_collections()