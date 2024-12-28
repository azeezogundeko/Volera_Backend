from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Literal, Optional, Union, Any, TypedDict

class UserContext(TypedDict):
    user_id: str
    session_id: Optional[str] = None
    focus_mode: Optional[str] = "default" 
    preferences: Optional[Dict[str, str]] = None 
    history: Optional[List[Dict[str, str]]] = None 
    session_start_time: Optional[datetime] = None


class History(TypedDict):
    speaker: Literal["assistant", "human"] 
    message: str
    timestamp: datetime = field(default_factory=datetime.now)


class MessageDict(TypedDict):
    chat_id: str | None
    content: str
    message_id: str
    title: str
    role: Literal["human", "assistant"] 


class WSMessage(TypedDict):
    user_id: str
    focus_mode: str
    files: List[str]
    message: Dict[str, MessageDict]
    history: List[Dict[str, History]]
    optimization_mode: Literal["fast", "balanced", "quality"] 

    

class Result(TypedDict):
    type: str
    content: str
    metadata: Dict[str, Any]  


class Timestamps(TypedDict):
    created_at: datetime = field(default_factory=datetime.now)


class TaskInfo(TypedDict):
    task_id: str
    status: Literal["pending", "in_progress", "completed", "failed"]  # e.g., pending, in_progress, completed, failed
  

class Performance(TypedDict):
    execution_time: Optional[float] = None  # in seconds


class TokenUsage(TypedDict):
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


class InputOutput(TypedDict):
    tokens: TokenUsage = field(default_factory=TokenUsage)


class AgentMetadata(TypedDict):
    task_info: TaskInfo
    performance: Performance = field(default_factory=Performance)
    input_output: InputOutput = field(default_factory=InputOutput)


class AgentResult(TypedDict):
    name: str
    content: dict
    metadata: Dict[str, AgentMetadata]

@dataclass
class SystemPromptPart:
    content: str
    part_kind: Literal['system-prompt'] = 'system-prompt'

@dataclass
class UserPromptPart:
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    part_kind: Literal['user-prompt'] = 'user-prompt'

@dataclass
class ToolReturnPart:
    content: Any
    part_kind: Literal['tool-return'] = 'tool-return'

@dataclass
class RetryPromptPart:
    content: Union[List[Dict[str, Any]], str]
    tool_name: Optional[str] = None
    tool_call_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    part_kind: Literal['retry-prompt'] = 'retry-prompt'

@dataclass
class TextPart:
    content: str
    part_kind: Literal['text'] = 'text'

@dataclass
class ArgsJson:
    args_json: str

@dataclass
class ArgsDict:
    args_dict: Dict[str, Any]

@dataclass
class ToolCallPart:
    tool_name: str
    args: Union[ArgsJson, ArgsDict]
    tool_call_id: Optional[str] = None
    part_kind: Literal['tool-call'] = 'tool-call'

@dataclass
class ModelRequest:
    parts: List[Union[SystemPromptPart, UserPromptPart, ToolReturnPart, RetryPromptPart]]
    kind: Literal['request'] = 'request'

@dataclass
class ModelResponse:
    parts: List[Union[TextPart, ToolCallPart]]
    timestamp: datetime = field(default_factory=datetime.now)
    kind: Literal['response'] = 'response'

ModelMessage = Union[ModelRequest, ModelResponse]
