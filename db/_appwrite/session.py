# from asyncio import gather
from asyncio import gather
from datetime import datetime
from typing import Dict, Any, Literal, Optional, List
from api.product.model import Product
# from datetime import datetime, timezone



from api.chat.model import Message,  Chat #, MessageImage
# from .base import async_appwrite
from utils.logging import logger
# from utils.websocket import ImageMetadata, SourceMetadata, ProductSchema
# from typing import TypedDict

from pydantic import BaseModel


# class ImageMetadata(TypedDict):
#     url: str
#     img_url: str
#     title: str

class FileMessage(BaseModel):
    fileData: bytes
    fileName: str
    fileExtension: str

class AppwriteSessionManager:
    # def __init__(self):
    #     """
    #     Initialize session management using existing async Appwrite client
    #     """


    #not supported yet
    async def process_files(self, file_ids: List[str]): ...
    #     if not file_ids:
    #         return []

    #     all_files = []

    #     for file_id in file_ids:
    #         try:
    #             file = await File.get_file_metadata(file_id)
    #             all_files.append(
    #                 ImageMetadata(
    #                     img_url="",
    #                     title
    #                 )
    #             )
    #         except Exception:
    #             continue


    async def start_session(
        self, 
        user_id: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new user session in Appwrite
        
        :param user_id: Unique identifier for the user
        :param metadata: Additional session metadata
        :param duration: Session duration in seconds
        :return: Session details
        """
        try:
            session_id = metadata["chat_id"]
            focus_mode = metadata.get("focus_mode")
            file_ids = metadata.get("file_ids")
            title = metadata.get("title")
            

            payload = {
                "title": title,
                "focus_mode": focus_mode,
                "file_ids": file_ids,
                # "user_id": user_id,
                "start_time": datetime.now().isoformat(),
            }

            await Chat.update(session_id, payload)
            # await create_message(chat_payload)
            logger.info(f"Created session for user {user_id}: {session_id}")
            return session_id

        except Exception as e:
            logger.error(f"Failed to create session: {str(e)}")
            raise

    async def log_messages(self, message_logs: Dict[str, Any]):
        # tasks = []
        # print(message_logs)
        document_id = Message.get_unique_id()
        products = message_logs.pop("original_products")

        # print(products)
        tasks = []
        for product in products:
            tasks.append(self.save_products(product))
        tasks.append(Message.create(document_id, message_logs))
        await gather(*tasks, return_exceptions=True)

    async def save_products(self, product: Dict[str, Any]):
        product_dict = dict(
            name=product["name"],
            brand=product["brand"],
            url=product["url"],
            current_price=product["current_price"],
            image=product["image"],
            features=product["features"] if product["features"] else [],
            specification=product["specification"] if product["specification"] else [],
            ratings=product["rating"],
            source=product["source"],
            original_price=product["original_price"],
            discount=product["discount"],
            reviews_count=product["rating_count"],
            currency=product["currency"]
        )
        await Product.create(product["product_id"], product_dict)

    async def log_message(
        self, 
        content: Any,
        session_id: str, 
        message_type: Literal["human", "assistant"], 
        ):
        message_id = Message.get_unique_id()
        await Message.create(message_id, dict(
            content=content,
            chat_id=session_id,
            role=message_type,
        ))




# Singleton instance for easy import and use
appwrite_session_manager = AppwriteSessionManager()