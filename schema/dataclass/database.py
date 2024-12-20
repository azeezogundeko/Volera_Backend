from dataclasses import dataclass
from typing import Literal, Dict, Any, List


@dataclass
class Message:
    content: str
    chat_id: str
    message_id: str
    role: Literal["human", "assistant"]
    metadata: Dict[str, Any]

MESSAGE_ATTRIBUTES = [
    {"key": "content", "size": 65535, "required": True},  # Increased size for longer messages
    {"key": "chat_id", "size": 255, "required": True},
    {"key": "message_id", "size": 255, "required": True},
    {"key": "role", "size": 20, "required": True},
    {"key": "metadata", "type": "json", "required": False},
    {"key": "created_at", "type": "datetime", "required": True}
]

@dataclass
class File:
    name: str
    field_id: str


@dataclass
class Chat:
    id: str
    title: str
    created_at: str
    focus_mode: str
    files: List[File]

CHAT_ATTRIBUTES = [
    {"key": "title", "size": 255, "required": True},
    {"key": "created_at", "type": "datetime", "required": True},
    {"key": "focus_mode", "size": 50, "required": True},
    {"key": "files", "type": "array", "required": False}
]