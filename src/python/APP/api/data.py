from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from common.config import settings, logger
from common.database import get_db
from common.device_payloads import build_realtime_data
from common.models import EnvMonitorData, Device
from common.iot_client import iot_client
from common.websocket_manager import manager as ws_manager

router = APIRouter(tags=["数据查询与同步"])

@router.get("/data/realtime/{device_id}")
def get_realtime_data(device_id: str, db: Session = Depends(get_db)):
    """获取设备最新实时数据（完整9项）。"""
    latest = (
        db.query(EnvMonitorData)
        .filter(EnvMonitorData.device_id == device_id)
        .order_by(EnvMonitorData.timestamp.desc())
        .first()
    )

    device = db.query(Device).filter(Device.device_id == device_id).first()
    is_online = device.is_online if device else False

    if not latest:
        return {
            "message": "暂无数据",
            "online": is_online,
            "data": None,
        }

    return {
        "message": "实时数据查询成功",
        "online": is_online,
        "data": build_realtime_data(latest),
    }


@router.get("/data/latest/{device_id}")
def get_latest_data(device_id: str, db: Session = Depends(get_db)):
    latest = (
        db.query(EnvMonitorData)
        .filter(EnvMonitorData.device_id == device_id)
        .order_by(EnvMonitorData.timestamp.desc())
        .first()
    )

    if not latest:
        logger.warning(f"设备 {device_id} 无数据记录")
        return {"message": "暂无数据"}

    logger.info(f"查询最新数据: {device_id}")
    return {
        "message": "最新数据查询成功",
        "data": build_realtime_data(latest),
    }


@router.get("/data/history/{device_id}")
def get_history_data(device_id: str, limit: int = 20, db: Session = Depends(get_db)):
    records = (
        db.query(EnvMonitorData)
        .filter(EnvMonitorData.device_id == device_id)
        .order_by(EnvMonitorData.timestamp.desc())
        .limit(limit)
        .all()
    )

    data_list = [build_realtime_data(r) for r in records]

    logger.info(f"查询历史数据: {device_id}，共 {len(data_list)} 条")
    return {"message": "历史数据查询成功", "count": len(data_list), "data": data_list}


@router.get("/sync")
def sync_data_from_huawei():
    if not settings.HUAWEI_IOTDA_ENABLED:
        raise HTTPException(status_code=400, detail="华为云功能未启用")

    if not settings.HUAWEI_IOTDA_REST_ENABLED:
        logger.info("REST API主动拉取已禁用，仅使用数据转发回调")
        return {"message": "REST API主动拉取已禁用，仅使用数据转发回调", "data": {}}

    logger.info("开始从华为云同步数据...")
    result = iot_client.pull_device_data(settings.HUAWEI_IOTDA_DEVICE_ID)
    return {"message": "数据同步完成", "data": result}


@router.get("/system/status/{device_id}")
def get_system_status(device_id: str, db: Session = Depends(get_db)):
    """获取系统连接状态（WiFi/MQTT/在线/WebSocket客户端数）。"""
    device = db.query(Device).filter(Device.device_id == device_id).first()
    is_online = device.is_online if device else False

    latest = (
        db.query(EnvMonitorData)
        .filter(EnvMonitorData.device_id == device_id)
        .order_by(EnvMonitorData.timestamp.desc())
        .first()
    )

    wifi_connected = False
    wifi_rssi = None
    wifi_ip = None
    mqtt_connected = is_online
    last_seen = None

    if latest:
        wifi_connected = latest.wifi_conn_state == 1 if latest.wifi_conn_state is not None else False
        wifi_rssi = latest.wifi_rssi
        wifi_ip = latest.wifi_ip
        if latest.timestamp:
            last_seen = latest.timestamp.isoformat()
            if datetime.utcnow() - latest.timestamp.replace(tzinfo=None) > timedelta(seconds=60):
                mqtt_connected = False

    return {
        "online": is_online,
        "wifi": wifi_connected,
        "wifi_rssi": wifi_rssi,
        "ip": wifi_ip,
        "mqtt": mqtt_connected,
        "ws_clients": len(getattr(ws_manager, '_connections', [])),
        "last_seen": last_seen,
        "huawei_enabled": settings.HUAWEI_IOTDA_ENABLED,
    }
