from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Dict, Any, List


@dataclass
class Message:
    content: str
    chat_id: str
    message_id: str
    role: Literal["human", "assistant"]
    metadata: str

MESSAGE_ATTRIBUTES = [
    {"key": "content", "size": 65535, "required": True}, 
    {"key": "chat_id", "size": 255, "required": True},
    {"key": "message_id", "size": 255, "required": True},
    {"key": "role", "size": 20, "required": True},
    {"key": "metadata", "type": "json", "required": False},
]

@dataclass
class File:
    name: str
    field_id: str


@dataclass
class Chat:
    title: str
    user_id: str
    end_time: str
    start_time: str
    focus_mode: str
    files: List[File]


CHAT_ATTRIBUTES = [
    {"key": "title", "size": 255, "required": True},
    {"key": "user_id", "size": 50, "required": True},
    {"key": "focus_mode", "size": 50, "required": True},
    {"key": "files", "type": "array", "required": False},
    {"key": "end_time", "type": "datetime", "required": True},
    {"key": "start_time", "type": "datetime", "required": True}
]