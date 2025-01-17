from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List


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
    content: str
    role: str
    created_at: datetime
    metadata: str 

class MessageSchema(BaseModel):
    total: int
    documents: List[MessageIn] = None
    
class MessageOut(BaseModel):
    chat: ChatOut
    messages: MessageSchema