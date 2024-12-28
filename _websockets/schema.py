from pydantic import BaseModel, Field
from typing import List, Literal
from datetime import datetime

class HistoryItem(BaseModel):
    speaker: str
    message: str
    timestamp: datetime

class MessageData(BaseModel):
    message_id: str = Field(alias="messageId")
    chat_id: str | None = Field(default=None, alias="chatId")
    content: str
    focus_mode: Literal["copilot", "comparison", "reviews", "all", "metrics", "insights"] = Field(default="copilot", alias="focusMode")
    optimization_mode: str = Field(default="speed", alias="optimizationMode")
    file_ids: List[str] | None = Field(default_factory=list, alias="fileIds")
    history: List[HistoryItem] | None = Field(default_factory=list)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True

class WebSocketMessage(BaseModel):
    type: str = "message"
    data: MessageData

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
