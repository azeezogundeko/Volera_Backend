from .model_base import AppwriteModelBase

from api.track.model import Product, PriceHistory, Feature
from api.chat.model import Chat, Message, File
from api.product.model import Product, Specification, Stores


AppwriteModelBase.register_model(Product)
AppwriteModelBase.register_model(Specification)
AppwriteModelBase.register_model(Stores)
# AppwriteModelBase.register_model(TrackedItem)
AppwriteModelBase.register_model(PriceHistory)
AppwriteModelBase.register_model(Feature)
AppwriteModelBase.register_model(Chat)
AppwriteModelBase.register_model(Message)
AppwriteModelBase.register_model(File)


async def prepare_database():
    await AppwriteModelBase.create_all_collections()