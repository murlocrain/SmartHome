"""
网关服务 - Pydantic 数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict


class ConnectionStatus(BaseModel):
    active_families: int = 0
    total_connections: int = 0


class PingMessage(BaseModel):
    type: str = Field("ping")


class PongMessage(BaseModel):
    type: str = Field("pong")
    timestamp: str = Field(...)
