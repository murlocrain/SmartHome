"""
兼容旧版单进程入口。

保留 start.sh 依赖的旧路由，同时复用 common/ 中的数据库、模型和 IoT 客户端，
避免继续维护一套重复的实现。
"""

import asyncio
import os
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from common.config import settings, logger
from common.database import SessionLocal, get_db, init_database
from common.huawei_callback import parse_huawei_callback_data, store_env_data
from common.iot_client import iot_client
from common.models import Device, EnvMonitorData, Family


app = FastAPI(title="智能家居数据服务", version="1.0")


@app.middleware("http")
async def log_all_requests(request: Request, call_next):
    if request.url.path not in ("/", "/favicon.ico"):
        body = None
        if request.method == "POST":
            try:
                body = (await request.body()).decode("utf-8")[:300]
            except Exception:
                body = None
        logger.info(f"[请求] {request.method} {request.url.path} 来源={request.client.host if request.client else '?'}")
        if body:
            logger.info(f"[请求体] {body}")
    return await call_next(request)


class ControlRequest(BaseModel):
    action: str


class DeviceResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    device_id: str
    name: Optional[str] = None
    device_type: str
    is_online: bool
    last_seen: Optional[datetime]
    created_at: datetime


class EnvDataResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    device_id: str
    mq2_adc: Optional[int] = None
    sht30_temp_raw: Optional[float] = None
    sht30_humi_raw: Optional[float] = None
    bh1750_raw: Optional[int] = None
    accel_x: Optional[int] = None
    accel_y: Optional[int] = None
    accel_z: Optional[int] = None
    gyro_x: Optional[int] = None
    gyro_y: Optional[int] = None
    gyro_z: Optional[int] = None
    mpu_temp_raw: Optional[float] = None
    pir_gpio: Optional[int] = None
    key_adc: Optional[int] = None
    uart_rx_len: Optional[int] = None
    uart_rx_hex: Optional[str] = None
    wifi_conn_state: Optional[int] = None
    wifi_rssi: Optional[int] = None
    wifi_ip: Optional[int] = None
    wifi_band: Optional[int] = None
    wifi_frequency: Optional[int] = None
    timestamp: datetime


@app.get("/")
async def root():
    return {"message": "智能家居数据服务", "docs": "http://localhost:8000/docs"}


@app.post("/")
def huawei_callback_fallback(request: dict, db: Session = Depends(get_db)):
    return huawei_device_callback(request, db)


@app.get("/devices", response_model=List[DeviceResponse])
def get_devices(db: Session = Depends(get_db)):
    return db.query(Device).all()


@app.post("/devices/register")
def register_device(db: Session = Depends(get_db)):
    device_id = settings.HUAWEI_IOTDA_DEVICE_ID
    if not device_id:
        raise HTTPException(status_code=400, detail="未配置华为云设备ID")

    device = db.query(Device).filter(Device.device_id == device_id).first()
    if device:
        return {"message": "设备已注册", "device": DeviceResponse.model_validate(device)}

    family = db.query(Family).filter(Family.name == "默认家庭").first()
    device = Device(
        device_id=device_id,
        name="环境监测设备",
        device_type="env_monitor",
        family_id=family.id if family else 1,
        is_online=True,
        last_seen=datetime.now(timezone.utc),
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return {"message": "设备注册成功", "device": DeviceResponse.model_validate(device)}


@app.get("/data/latest", response_model=EnvDataResponse)
def get_latest_data(db: Session = Depends(get_db)):
    data = db.query(EnvMonitorData).order_by(EnvMonitorData.timestamp.desc()).first()
    if not data:
        raise HTTPException(status_code=404, detail="暂无数据")
    return EnvDataResponse.model_validate(data)


@app.get("/data/history", response_model=List[EnvDataResponse])
def get_history_data(limit: int = Query(10, ge=1, le=100), db: Session = Depends(get_db)):
    records = (
        db.query(EnvMonitorData)
        .order_by(EnvMonitorData.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [EnvDataResponse.model_validate(record) for record in records]


def _send_control(command_name: str, paras: dict) -> dict:
    result = iot_client.send_command(command_name, paras)
    if result.get("success"):
        return result
    raise HTTPException(status_code=500, detail=result.get("error", "命令下发失败"))


@app.post("/control/light")
def control_light(request: ControlRequest):
    if request.action not in ["ON", "OFF"]:
        raise HTTPException(status_code=400, detail="action必须为ON或OFF")
    result = _send_control("light_control", {"onoff": request.action})
    return {"success": True, "message": f"灯光已{request.action}", "response": result}


@app.post("/control/motor")
def control_motor(request: ControlRequest):
    if request.action not in ["ON", "OFF"]:
        raise HTTPException(status_code=400, detail="action必须为ON或OFF")
    result = _send_control("motor_control", {"onoff": request.action})
    return {"success": True, "message": f"电机已{request.action}", "response": result}


@app.post("/control/beep")
def control_beep():
    result = _send_control("beep_play", {})
    return {"success": True, "message": "蜂鸣器已播放", "response": result}


@app.post("/control/beep_song")
def control_beep_song(id: int = 0):
    result = _send_control("beep_song", {"id": id})
    return {"success": True, "message": f"歌曲{id}已播放", "response": result}


def sync_huawei_data(db: Session) -> dict:
    shadow = iot_client.get_device_shadow(settings.HUAWEI_IOTDA_DEVICE_ID)
    if not shadow:
        return {"synced": 0, "message": "获取设备影子失败"}
    if "error" in shadow:
        return {
            "synced": 0,
            "message": shadow["error"],
            "suggestion": shadow.get("suggestion", ""),
        }

    properties = {}
    for service in shadow.get("shadow", []):
        reported = service.get("reported", {})
        properties.update(reported.get("properties", {}))

    if not properties:
        return {"synced": 0, "message": "无属性数据"}

    store_env_data(
        db,
        settings.HUAWEI_IOTDA_DEVICE_ID,
        properties,
        {"shadow": shadow},
    )
    return {
        "synced": 1,
        "properties": list(properties.keys()),
        "message": "成功同步数据",
    }


@app.post("/sync")
def sync_data(db: Session = Depends(get_db)):
    return sync_huawei_data(db)


CALLBACK_HIT_COUNT = 0


@app.get("/api/v1/devices/huawei-callback")
@app.get("/huawei-callback")
def huawei_callback_diag():
    global CALLBACK_HIT_COUNT
    return {
        "status": "ok",
        "message": "回调端点可达，等待华为云POST数据",
        "post_hit_count": CALLBACK_HIT_COUNT,
        "port": 8000,
    }


@app.post("/api/v1/devices/huawei-callback")
@app.post("/huawei-callback")
def huawei_device_callback(request: dict, db: Session = Depends(get_db)):
    global CALLBACK_HIT_COUNT
    CALLBACK_HIT_COUNT += 1
    logger.info(f"收到华为云回调数据(第{CALLBACK_HIT_COUNT}次): {str(request)[:300]}...")

    try:
        payload = request.get("notify_data", request)
        device_id = (
            payload.get("header", {}).get("device_id")
            or request.get("device_id")
            or settings.HUAWEI_IOTDA_DEVICE_ID
        )
        properties = parse_huawei_callback_data(payload)
        if not properties:
            logger.warning("回调数据中无可解析属性")
            return {"code": "1000", "message": "数据格式错误：无属性字段"}

        store_env_data(db, device_id, properties, request)
        return {"code": "0", "message": "success"}
    except Exception as exc:
        logger.error(f"处理华为云回调数据失败: {exc}")
        db.rollback()
        return {"code": "1001", "message": f"处理失败: {str(exc)}"}


async def periodic_sync():
    while True:
        db = SessionLocal()
        try:
            result = sync_huawei_data(db)
            logger.info(f"定时同步完成: {result}")
        except Exception as exc:
            logger.error(f"定时同步失败: {exc}")
        finally:
            db.close()
        await asyncio.sleep(settings.SYNC_INTERVAL)


@app.on_event("startup")
async def startup_event():
    init_database()

    db = SessionLocal()
    try:
        device_id = settings.HUAWEI_IOTDA_DEVICE_ID
        if device_id and not db.query(Device).filter(Device.device_id == device_id).first():
            family = db.query(Family).filter(Family.name == "默认家庭").first()
            device = Device(
                device_id=device_id,
                name="环境监测设备",
                device_type="env_monitor",
                family_id=family.id if family else 1,
                is_online=True,
                last_seen=datetime.now(timezone.utc),
            )
            db.add(device)
            db.commit()
            logger.info("设备已注册")
    finally:
        db.close()

    if settings.HUAWEI_IOTDA_REST_ENABLED:
        asyncio.create_task(periodic_sync())
        logger.info("定时同步任务已启动")
    else:
        logger.info("REST API主动拉取已禁用，仅使用数据转发回调")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("服务正在关闭...")


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("APP_PORT", "8000"))
    host = os.getenv("APP_HOST", "0.0.0.0")

    logger.info(f"启动服务: http://{host}:{port}")
    logger.info(f"回调接口: http://{host}:{port}/api/v1/devices/huawei-callback")
    logger.info(f"API文档: http://localhost:{port}/docs")

    uvicorn.run(app, host=host, port=port)
