from datetime import datetime
from db._appwrite.model_base import AppwriteField, AppwriteModelBase

class Chat(AppwriteModelBase):
    collection_id = "chats"

    user_id = AppwriteField(size=255)
    title: str = AppwriteField(size=255, required=False)
    start_time: datetime = AppwriteField(required=False, type="datetime")
    focus_mode: str = AppwriteField(required=False, size=50)
    index = AppwriteField(type="index", index_type="unique", index_attr=["user_id"])
    title_index = AppwriteField(type="index", index_type="text", index_attr=["title"])
    

class File(AppwriteModelBase):
    collection_id = "files"

    name: str = AppwriteField(size=255)
    file_extension: str = AppwriteField(size=10)
    chat_id: str = AppwriteField(required=True, size=255)
    index = AppwriteField(type="index", index_type="unique", index_attr=["chat_id"])


class MessageImage(AppwriteModelBase):
    collection_id = "message_images"

    name: str = AppwriteField(size=255)
    file_extension: str = AppwriteField(size=10)
    message_id: str = AppwriteField(required=True, size=255)
    index = AppwriteField(type="index", index_type="unique", index_attr=["message_id"])

class Message(AppwriteModelBase):
    collection_id = "messages"

    content: str = AppwriteField(size=65535)
    # is_deleted: bool = AppwriteField(required=False, type="bool", default=False)
    role: str = AppwriteField(size=255)
    metadata: dict = AppwriteField(type="json", required=False)
    content_index = AppwriteField(type="index", index_type="text", index_attr=["content"])
    id_index = AppwriteField(type="index", index_type="unique", index_attr=["chat_id"])
    chat_id: str = AppwriteField(required=True, size=255)