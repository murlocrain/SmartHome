from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class AIChatRequest(BaseModel):
    message: str = Field(..., description="要对 AI 说的话")


class AIChatResponse(BaseModel):
    message: str
    reply: str
    model: str


class AIAgentRequest(BaseModel):
    message: str = Field(..., description="自然语言指令")


class AIAgentResponse(BaseModel):
    message: str
    reply: str
    parsed: dict
    device_result: Optional[dict] = None
    current_env: Optional[str] = None
    env_suggestion: Optional[str] = None


class SceneRuleCreate(BaseModel):
    family_id: int
    name: str
    scene_id: str
    conditions: dict
    actions: dict


class SceneRuleResponse(BaseModel):
    id: int
    family_id: int
    name: str
    scene_id: str
    conditions: dict
    actions: dict
    is_enabled: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SceneEventLogResponse(BaseModel):
    id: int
    family_id: int
    rule_id: Optional[int]
    scene_id: Optional[str]
    event_type: str
    description: Optional[str]
    suggestion: Optional[str]
    details: Optional[dict]
    created_at: datetime

    class Config:
        from_attributes = True


class SceneEvent(BaseModel):
    scene_id: str
    name: str
    description: str
    suggestion: str
    priority: str = "info"


class RoomStateResponse(BaseModel):
    family_id: int
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    illumination: Optional[int] = None
    has_person: bool = False
    smoke_detected: bool = False
    wifi_connected: bool = True
    last_update: Optional[str] = None
