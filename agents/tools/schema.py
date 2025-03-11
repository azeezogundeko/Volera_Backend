from pydantic import BaseModel

from datetime import datetime
from typing import List, Dict, Any, Optional
import json

from pydantic_ai.messages import (
    ModelMessage,
    ModelMessagesTypeAdapter,
    ModelRequest,
    ModelResponse,
    ToolCallPart,
    TextPart,
    UserPromptPart,
)


class FilterAttributes(BaseModel):
    features: Optional[List[str]] = None
    category: Optional[str] = None

class PriceFilter(BaseModel):
    max: Optional[float] = None
    min: Optional[float] = None

class SearchFilter(BaseModel):
    price: Optional[PriceFilter] = None
    attributes: Optional[FilterAttributes] = None

class WebSearchRequest(BaseModel):
    search_query: str 
    filter: Optional[SearchFilter] = None
    n_k: int
    description: str
    mode: str 



# Assuming the dataclasses ModelRequest, ModelResponse, UserPromptPart, ToolCallPart, and TextPart have been imported

def extract_dataclass_messages(messages: List[Any]) -> Dict[str, List[str]]:
    human_messages = []
    ai_messages = []
    
    for message in messages:
        # Check for human messages in ModelRequest parts
        if isinstance(message, ModelRequest):
            for part in message.parts:
                if isinstance(part, UserPromptPart):
                    # part.content can be a str or a sequence (for images/audio, etc.)
                    if isinstance(part.content, str):
                        human_messages.append(part.content)
                    else:
                        # Convert a sequence of content items to a string representation
                        human_messages.append(" ".join(str(item) for item in part.content))
                        
        # Check for AI messages in ModelResponse parts
        elif isinstance(message, ModelResponse):
            for part in message.parts:
                # If the part is a tool call, try to extract the "content" from its arguments
                if isinstance(part, ToolCallPart):
                    # If args is a dict
                    if isinstance(part.args, dict):
                        if "content" in part.args:
                            ai_messages.append(part.args["content"])
                    # If args is a string, attempt to parse it as JSON
                    elif isinstance(part.args, str):
                        try:
                            args_dict = json.loads(part.args)
                            if "content" in args_dict:
                                ai_messages.append(args_dict["content"])
                        except Exception:
                            ai_messages.append(part.args)
                # Also check for simple text responses from the model
                elif hasattr(part, "content"):
                    ai_messages.append(part.content)
    
    return {"human_message": human_messages, "ai_message": ai_messages}

