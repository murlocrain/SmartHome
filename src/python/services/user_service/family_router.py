from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from common.database import get_db
from common.models import User, Family, FamilyMember, Room
from common.security import get_current_user_id
from common.schemas.common import ResponseModel
from .schemas import FamilyCreate, FamilyResponse, FamilyMemberAdd, FamilyMemberResponse, RoomCreate, RoomResponse

router = APIRouter(prefix="/family", tags=["家庭管理"])


@router.post("/create", response_model=ResponseModel[FamilyResponse])
def create_family(family_data: FamilyCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    family = Family(name=family_data.name, owner_id=user_id)
    db.add(family)
    db.flush()
    member = FamilyMember(family_id=family.id, user_id=user_id, role="admin")
    db.add(member)
    db.commit()
    db.refresh(family)
    return ResponseModel(data=FamilyResponse.model_validate(family))


@router.get("/list", response_model=ResponseModel[list[FamilyResponse]])
def get_my_families(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    families = (
        db.query(Family)
        .join(FamilyMember, Family.id == FamilyMember.family_id)
        .filter(FamilyMember.user_id == user_id)
        .all()
    )
    return ResponseModel(data=[FamilyResponse.model_validate(f) for f in families])


@router.get("/{family_id}", response_model=ResponseModel[FamilyResponse])
def get_family(family_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    family = db.query(Family).filter(Family.id == family_id).first()
    if not family:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="家庭不存在")
    return ResponseModel(data=FamilyResponse.model_validate(family))


@router.post("/{family_id}/members", response_model=ResponseModel[FamilyMemberResponse])
def add_member(family_id: int, member_data: FamilyMemberAdd, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    existing = db.query(FamilyMember).filter(
        FamilyMember.family_id == family_id,
        FamilyMember.user_id == member_data.user_id,
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="成员已存在")
    member = FamilyMember(family_id=family_id, user_id=member_data.user_id, role=member_data.role)
    db.add(member)
    db.commit()
    db.refresh(member)
    return ResponseModel(data=FamilyMemberResponse.model_validate(member))


@router.get("/{family_id}/members", response_model=ResponseModel[list[FamilyMemberResponse]])
def get_members(family_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    members = db.query(FamilyMember).filter(FamilyMember.family_id == family_id).all()
    return ResponseModel(data=[FamilyMemberResponse.model_validate(m) for m in members])


@router.delete("/{family_id}/members/{user_id_to_remove}", response_model=ResponseModel)
def remove_member(family_id: int, user_id_to_remove: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    member = db.query(FamilyMember).filter(
        FamilyMember.family_id == family_id,
        FamilyMember.user_id == user_id_to_remove,
    ).first()
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="成员不存在")
    db.delete(member)
    db.commit()
    return ResponseModel(message="成员已移除")


@router.post("/{family_id}/rooms", response_model=ResponseModel[RoomResponse])
def create_room(family_id: int, room_data: RoomCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    room = Room(name=room_data.name, family_id=family_id)
    db.add(room)
    db.commit()
    db.refresh(room)
    return ResponseModel(data=RoomResponse.model_validate(room))


@router.get("/{family_id}/rooms", response_model=ResponseModel[list[RoomResponse]])
def get_rooms(family_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    rooms = db.query(Room).filter(Room.family_id == family_id).all()
    return ResponseModel(data=[RoomResponse.model_validate(r) for r in rooms])
