from datetime import datetime
from ast import literal_eval
from typing import Any
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict


class FileSchema(BaseModel):
    id : str = Field(serialization_alias="fileId", alias="$id")
    name: str = Field(serialization_alias="fileName")
    file_extension: str = Field(serialization_alias="fileExtension")

class FileOut(BaseModel):
    message: str
    files: List[FileSchema]

class ChatOut(BaseModel):
    user_id: str
    start_time: datetime
    id: str
    created_at: datetime
    files: Optional[List[FileSchema]] = []
    
class MessageIn(BaseModel):
    id: str
    content: str | None = None
    role: str
    created_at: datetime
    metadata: str | None = None
    images: Optional[List[Dict[str, str]]] = []
    products: Optional[List[Dict[str, Any]]] = []
    sources: Optional[List[Dict[str, str]]] = []

    @field_validator("images", "products", "sources", mode="before")
    def validate_fields(cls, v):
        return [literal_eval(item) for item in v]


class MessageSchema(BaseModel):
    total: int
    documents: List[MessageIn] = None
    
class MessageOut(BaseModel):
    chat: ChatOut
    messages: MessageSchema