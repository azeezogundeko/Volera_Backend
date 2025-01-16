from datetime import datetime
from db._appwrite.model_base import AppwriteModelBase
from db._appwrite.fields import AppwriteField


class Chat(AppwriteModelBase):
    collection_id = "chats"

    user_id = AppwriteField(size=255)
    title: str = AppwriteField(size=255, required=False)
    start_time: datetime = AppwriteField(required=False, type="datetime")
    focus_mode: str = AppwriteField(required=False, size=50)
    index = AppwriteField(type="index", index_type="key", index_attr=["user_id"])
    title_index = AppwriteField(type="index", index_type="text", index_attr=["title"])
    

class File(AppwriteModelBase):
    collection_id = "files"

    name: str = AppwriteField(size=255)
    file_extension: str = AppwriteField(size=10)
    chat_id: str = AppwriteField(required=True, size=255)
    index = AppwriteField(type="index", index_type="key", index_attr=["chat_id"])


class MessageImage(AppwriteModelBase):
    collection_id = "message_images"

    name: str = AppwriteField(size=255)
    file_extension: str = AppwriteField(size=10)
    message_id: str = AppwriteField(required=True, size=255)
    index = AppwriteField(type="index", index_type="key", index_attr=["message_id"])


class SavedChat(AppwriteModelBase):
    collection_id = "saved_chats"

    chat_id: str = AppwriteField(required=True, size=255)
    index = AppwriteField(type="index", index_type="key", index_attr=["chat_id"])
    
    

class Message(AppwriteModelBase):
    collection_id = "messages"

    content: str = AppwriteField(size=65535)
    # is_deleted: bool = AppwriteField(required=False, type="bool", default=False)
    role: str = AppwriteField(size=255)
    metadata: dict = AppwriteField(type="json", required=False)
    chat_id: str = AppwriteField(required=True, size=255)
    id_index = AppwriteField(type="index", index_type="key", index_attr=["chat_id"])
    content_index = AppwriteField(type="index", index_type="fulltext", index_attr=["content"])