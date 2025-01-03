from datetime import datetime
from db._appwrite.model_base import AppwriteField, AppwriteModelBase

class Chat(AppwriteModelBase):
    collection_id = "chats"

    user_id = AppwriteField(size=255)
    title: str = AppwriteField(size=255, required=False)
    start_time: datetime = AppwriteField(required=False, type="datetime")
    focus_mode: str = AppwriteField(required=False, size=50)
    

class File(AppwriteModelBase):
    collection_id = "files"

    name: str = AppwriteField(size=255)
    file_extension: str = AppwriteField(size=10)
    chat_id: str = AppwriteField(required=True, size=255)


class Message(AppwriteModelBase):
    collection_id = "messages"

    content: str = AppwriteField(size=65535)
    role: str = AppwriteField(size=20)
    metadata: dict = AppwriteField(type="json", required=False)