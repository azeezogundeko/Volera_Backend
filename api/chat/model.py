from __future__ import annotations
from typing import List, Literal
import re
from datetime import datetime
from db._appwrite.model_base import AppwriteModelBase
from db._appwrite.fields import AppwriteField
from appwrite.query import Query


class Chat(AppwriteModelBase):
    collection_id = "chats"

    user_id = AppwriteField(size=255)
    title: str = AppwriteField(size=255, required=False)
    start_time: datetime = AppwriteField(required=False, type="datetime")
    focus_mode: str = AppwriteField(required=False, size=50)
    is_created: bool = AppwriteField(required=False, type=bool, default=False)
    file_ids: List[str] = AppwriteField(required=False, type="array", default=[])
    index = AppwriteField(type="index", index_type="key", index_attr=["user_id"])
    title_index = AppwriteField(type="index", index_type="fulltext", index_attr=["title"])
    

class File(AppwriteModelBase):
    collection_id = "files"

    name: str = AppwriteField(size=255)
    user_id: str = AppwriteField(required=False, size=255)
    file_extension: str = AppwriteField(size=10)
    # chat_id: str = AppwriteField(required=False, size=255)

    @classmethod
    async def get_or_create(cls, user_id: str, file, name: str, file_extension: str)-> File:
        try:
            file_id = cls.hash(name + "_" + user_id)
            file_id = re.sub(r'[^a-zA-Z0-9_.-]', '', file_id)
            if len(file_id) > 36:
                file_id = file_id[:36]
            doc = await cls.list(queries=[Query.equal("chat_id", file_id), Query.equal("user_id", user_id)])
            return doc["documents"][0]
        except Exception as e:
            print(str(e))
            document_id = cls.get_unique_id()
            await cls.create_file(document_id, file)
            return await cls.create(document_id, {"user_id": user_id, "name": name, "file_extension": file_extension})

    # async def create_files(cls, List[])


class MessageImage(AppwriteModelBase):
    collection_id = "message_images"

    image_url: str = AppwriteField(size=255)
    message_id: str = AppwriteField(required=True, size=255)
    title: str = AppwriteField(size=255)
    url: str = AppwriteField(size=255)


    # name: str = AppwriteField(size=255)
    # file_extension: str = AppwriteField(size=10)
    # message_id: str = AppwriteField(required=True, size=255)
    # index = AppwriteField(type="index", index_type="key", index_attr=["message_id"])


class SavedChat(AppwriteModelBase):
    collection_id = "saved_chats"

    chat_id: str = AppwriteField(required=True, size=255)
    index = AppwriteField(type="index", index_type="key", index_attr=["chat_id"])
    
    

class Message(AppwriteModelBase):
    collection_id = "messages"

    content: str = AppwriteField(size=65535, required=False)
    # is_deleted: bool = AppwriteField(required=False, type="bool", default=False)
    role: Literal["human", "assistant"] = AppwriteField(size=20)
    metadata: dict = AppwriteField(type="json", required=False)
    chat_id: str = AppwriteField(required=True, size=255)
    sources: str = AppwriteField(required=False, type="array", default=[])
    images: List[dict] = AppwriteField(required=False, type="array", default=[])
    type: Literal["product", "message", "image_search", "sources"] = AppwriteField(default="message", size=20)
    products: List[dict] = AppwriteField(required=False, type="array", default=[])
    # product_ids: List[str] = AppwriteField(required=False, type="array", default=[])
    content_index = AppwriteField(type="index", index_type="fulltext", index_attr=["content"])
    id_index = AppwriteField(type="index", index_type="key", index_attr=["chat_id"])