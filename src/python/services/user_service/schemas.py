from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[str] = None
    phone: Optional[str] = None
    password: str = Field(..., min_length=6, max_length=128)


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool
    privacy_settings: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None


class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6, max_length=128)


class PrivacySettingsUpdate(BaseModel):
    personalization: Optional[bool] = None
    data_collection: Optional[bool] = None


class FamilyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class FamilyResponse(BaseModel):
    id: int
    name: str
    owner_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class FamilyMemberAdd(BaseModel):
    user_id: int
    role: str = Field(default="member")


class FamilyMemberResponse(BaseModel):
    id: int
    family_id: int
    user_id: int
    role: str
    joined_at: datetime

    class Config:
        from_attributes = True


class RoomCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class RoomResponse(BaseModel):
    id: int
    name: str
    family_id: int
    created_at: datetime

    class Config:
        from_attributes = True
