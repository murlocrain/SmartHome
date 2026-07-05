from pydantic import BaseModel, Field
from typing import Optional


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="用户消息")


class ChatResponse(BaseModel):
    message: str
    reply: str
    model: str


class AgentControlRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="自然语言控制指令")


class AgentControlResponse(BaseModel):
    message: str
    reply: str
    intent: Optional[str] = None
    target: Optional[str] = None
    action: Optional[str] = None
    device_result: Optional[dict] = None
    current_env: Optional[str] = None
    suggestion: Optional[str] = None


class StreamChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="用户消息")
    mode: str = Field(default="chat", pattern="^(chat|agent)$", description="chat=闲聊, agent=控制模式")
