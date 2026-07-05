from typing import Optional
from pydantic import BaseModel, Field


class ControlRequest(BaseModel):
    action: str = Field(..., pattern="^(ON|OFF)$")
    device_id: Optional[str] = None


class ControlResponse(BaseModel):
    message: str
    status: str
    command_name: str
    paras: dict


class DeviceRegisterRequest(BaseModel):
    device_id: str
    device_type: str = "env_monitor"
    name: Optional[str] = None
    family_id: int = 1


class DeviceQueryResponse(BaseModel):
    message: str
    device: Optional[dict] = None
    raw_data: Optional[dict] = None


class DeviceListResponse(BaseModel):
    message: str
    count: int = 0
    devices: list = []


class SyncResponse(BaseModel):
    message: str
    data: dict


class LatestDataResponse(BaseModel):
    message: str
    data: Optional[dict] = None


# ==================== AI 相关 ====================
class AIChatRequest(BaseModel):
    message: str = Field(..., description="要对 AI 说的话，例如：你好")


class AIChatResponse(BaseModel):
    message: str
    reply: str
    model: str


class AIAgentRequest(BaseModel):
    message: str = Field(..., description="自然语言指令，例如：帮我把灯打开")


class AIAgentResponse(BaseModel):
    message: str
    reply: str
    parsed: dict
    device_result: Optional[dict] = None
    current_env: Optional[dict] = None
    env_suggestion: Optional[str] = None
