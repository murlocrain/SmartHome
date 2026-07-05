from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from common.config import logger
from common.database import get_db
from common.models import User
from common.security import create_access_token, create_refresh_token, decode_token, get_password_hash, verify_password, verify_token, get_current_user_id
from common.schemas.common import ResponseModel, Token
from .schemas import UserCreate, UserLogin, UserResponse, UserUpdate, PasswordChange, PrivacySettingsUpdate
from pydantic import BaseModel


class RefreshTokenRequest(BaseModel):
    refresh_token: str

router = APIRouter(prefix="/auth", tags=["认证"])


def get_current_user(
    payload: dict = Depends(verify_token),
    db: Session = Depends(get_db),
) -> User:
    user_id = int(payload["sub"])
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")
    return user


@router.post("/register", response_model=ResponseModel[UserResponse])
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在")
    user = User(
        username=user_data.username,
        email=user_data.email,
        phone=user_data.phone,
        hashed_password=get_password_hash(user_data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info(f"新用户注册: {user.username}")
    return ResponseModel(data=UserResponse.model_validate(user))


@router.post("/login", response_model=ResponseModel[Token])
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == login_data.username).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    token_data = {"sub": str(user.id), "username": user.username}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    logger.info(f"用户登录: {user.username}")
    return ResponseModel(data=Token(access_token=access_token, refresh_token=refresh_token))


@router.post("/refresh", response_model=ResponseModel[Token])
def refresh_token(data: RefreshTokenRequest, db: Session = Depends(get_db)):
    """使用 refresh_token 刷新 access_token。"""
    payload = decode_token(data.refresh_token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的refresh_token")
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌类型不正确")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的令牌")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")

    token_data = {"sub": str(user.id), "username": user.username}
    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)
    logger.info(f"用户刷新token: {user.username}")
    return ResponseModel(data=Token(access_token=new_access_token, refresh_token=new_refresh_token))


@router.get("/me", response_model=ResponseModel[UserResponse])
def get_me(user: User = Depends(get_current_user)):
    return ResponseModel(data=UserResponse.model_validate(user))


@router.put("/me", response_model=ResponseModel[UserResponse])
def update_me(update_data: UserUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return ResponseModel(data=UserResponse.model_validate(user))


@router.post("/change-password", response_model=ResponseModel)
def change_password(password_data: PasswordChange, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(password_data.old_password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="旧密码错误")
    user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    return ResponseModel(message="密码修改成功")


@router.get("/privacy", response_model=ResponseModel)
def get_privacy_settings(user: User = Depends(get_current_user)):
    return ResponseModel(data=user.privacy_settings or {})


@router.put("/privacy", response_model=ResponseModel)
def update_privacy_settings(settings_data: PrivacySettingsUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.privacy_settings is None:
        user.privacy_settings = {}
    if settings_data.personalization is not None:
        user.privacy_settings["personalization"] = settings_data.personalization
    if settings_data.data_collection is not None:
        user.privacy_settings["data_collection"] = settings_data.data_collection
    db.commit()
    db.refresh(user)
    return ResponseModel(data=user.privacy_settings)
