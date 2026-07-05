from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from common.config import settings, logger
from common.database import get_db
from common.models import Device, Family
from common.iot_client import iot_client
from APP.schemas import DeviceRegisterRequest, DeviceQueryResponse, DeviceListResponse

router = APIRouter(tags=["设备管理"])


@router.post("/devices/register")
def register_device(request: DeviceRegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(Device).filter(Device.device_id == request.device_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="设备已存在")

    device = Device(
        device_id=request.device_id,
        device_type=request.device_type,
        name=request.name or request.device_type,
        family_id=request.family_id,
        is_online=True,
        last_seen=datetime.now(timezone.utc),
    )
    db.add(device)
    db.commit()
    logger.info(f"新设备注册成功: {request.device_id}")
    return {"message": "设备注册成功", "device_id": request.device_id}


@router.get("/devices/list", response_model=DeviceListResponse)
def list_devices(db: Session = Depends(get_db)):
    devices = db.query(Device).all()
    device_list = []
    for d in devices:
        device_list.append({
            "id": d.id,
            "device_id": d.device_id,
            "device_type": d.device_type,
            "name": d.name,
            "is_online": d.is_online,
            "last_seen": d.last_seen,
            "created_at": d.created_at,
        })
    logger.info(f"列出设备列表，共 {len(device_list)} 台设备")
    return {"message": "设备列表获取成功", "count": len(device_list), "devices": device_list}


@router.get("/devices/{device_id}", response_model=DeviceQueryResponse)
def query_device(device_id: str, db: Session = Depends(get_db)):
    if settings.HUAWEI_IOTDA_ENABLED and settings.HUAWEI_IOTDA_REST_ENABLED:
        result = iot_client.query_device(device_id)
        if result.get("success"):
            logger.info(f"从华为云查询设备信息成功: {device_id}")
            return {"message": "设备信息查询成功", "device": result["data"], "raw_data": result}

    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        logger.warning(f"设备 {device_id} 未找到")
        raise HTTPException(status_code=404, detail="设备未找到")

    return {
        "message": "设备信息查询成功（本地数据库）",
        "device": {
            "device_id": device.device_id,
            "device_type": device.device_type,
            "name": device.name,
            "is_online": device.is_online,
            "last_seen": device.last_seen,
        },
    }
