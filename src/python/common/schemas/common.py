from pydantic import BaseModel, Field
from typing import Optional, Generic, TypeVar
from datetime import datetime

T = TypeVar("T")


class ResponseModel(BaseModel, Generic[T]):
    code: int = 200
    message: str = "success"
    data: Optional[T] = None


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
