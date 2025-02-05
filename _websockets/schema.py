from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime

class HistoryItem(BaseModel):
    speaker: str
    message: str
    timestamp: datetime

class MessageData(BaseModel):
    message_id: str = Field(alias="messageId")
    chat_id: str | None = Field(default=None, alias="chatId")
    content: str
    class Config:
        allow_population_by_field_name = True

class FileMessage(BaseModel):
    fileData: bytes
    fileName: str
    fileExtension: str

class WebSocketMessage(BaseModel):
    type: str | None = "message"
    data: MessageData
    focus_mode: str = Field(alias="focusMode", default="all")
    parent_message_id: str = Field(alias="parentMessageId",default=None)
    optimization_mode: str = Field(default="fast", alias="optimizationMode")
    file_ids: Optional[List[str]]  = []
    currentProducts: List[Any] = []
    currentFilters: Dict[str, Any] = None
    # history: List[HistoryItem] | None = Field(default_factory=list)

    class Config:
        allow_population_by_field_name = True


class RequestPayload(BaseModel):
    message: str
    currentProducts: List[Any]
    currentFilters: Dict[str, Any]

class RequestWebsockets(BaseModel):
    type: str
    data: RequestPayload
    # messageId: str