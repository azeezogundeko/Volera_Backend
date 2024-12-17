from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Literal, Optional, Union, Any


@dataclass
class UserContext:
    user_id: str
    session_id: Optional[str] = None
    focus_mode: Optional[str] = "default" 
    preferences: Optional[Dict[str, str]] = None 
    history: Optional[List[Dict[str, str]]] = None 
    session_start_time: Optional[datetime] = None

@dataclass
class History:
    speaker: Literal["assistant", "human"] 
    message: str
    timestamp: datetime

@dataclass
class Message:
    content: str
    chat_id: str
    message_id: str
    role: Literal["human", "assistant"] 

@dataclass
class WSMessage:
    user_id: str
    focus_mode: str
    files: List[str]
    message: Dict[str, Message]
    history: List[Dict[str, History]]
    optimization_mode: Literal["fast", "balanced", "quality"] 

    
@dataclass
class Result:
    type: str
    content: str
    metadata: Dict[str, Any]  

@dataclass
class Timestamps:
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class TaskInfo:
    task_id: str
    status: Literal["pending", "in_progress", "completed", "failed"]  # e.g., pending, in_progress, completed, failed
  
@dataclass
class Performance:
    execution_time: Optional[float] = None  # in seconds

@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

@dataclass
class InputOutput:
    tokens: TokenUsage = field(default_factory=TokenUsage)

@dataclass
class AgentMetadata:
    task_info: TaskInfo
    performance: Performance = field(default_factory=Performance)
    input_output: InputOutput = field(default_factory=InputOutput)

@dataclass
class AgentResult:
    name: str
    content: Dict[str, Any]
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
