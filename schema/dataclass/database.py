from typing import Literal, List
from dataclasses import asdict, dataclass


@dataclass
class MessageDT:
    content: str
    chat_id: str
    role: Literal["human", "assistant"]
    metadata: str

    def to_dict(self):
        return asdict(self)

MESSAGE_ATTRIBUTES = [
    {"key": "content", "size": 65535, "required": True}, 
    {"key": "chat_id", "size": 255, "required": True},
    # {"key": "message_id", "size": 255, "required": True},
    {"key": "role", "size": 20, "required": True},
    {"key": "metadata", "type": "json", "required": False},
]

@dataclass
class FileDT:
    name: str
    field_id: str


@dataclass
class ChatDT:
    title: str
    user_id: str
    start_time: str
    focus_mode: str
    files: List[FileDT]

    def to_dict(self):
        return asdict(self)


CHAT_ATTRIBUTES = [
    {"key": "title", "size": 255, "required": False},
    {"key": "user_id", "size": 50, "required": True},
    {"key": "focus_mode", "size": 50, "required": False},
    {"key": "files", "type": "array", "required": False},
    {"key": "start_time", "type": "datetime", "required": True}
]