import json
from datetime import datetime, timezone, timedelta

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Request, Body
from sqlalchemy.orm import Session
import requests as http_requests

from common.config import settings, logger
from common.control_utils import color_to_int
from common.database import get_db
from common.device_payloads import build_realtime_data
from common.huawei_callback import parse_huawei_callback_data, store_env_data
from common.models import Device, EnvMonitorData, AIPrediction
from common.iot_client import iot_client
from common.security import get_current_user_id
from .schemas import ControlRequest, ControlResponse, DeviceRegisterRequest, BindDeviceRequest, DeviceListResponse, LatestDataResponse, DeviceStatusResponse
from .schemas import LightColorRequest, LightBrightnessRequest, LightModeRequest, MotorSpeedRequest, BeepSongRequest, ModeRequest
from .schemas import DataQualityRequest, DataStatsRequest, DataValidateRequest, DataExportRequest
from common.data_quality import quality_report
from common.data_stats import distribution, correlation, trends, frequency_report
from common.data_validator import validate_record, detect_anomalies, recommend_fields
import csv
import io

# 业务路由 (前缀 /api/v1 通过 main.py 添加)
router = APIRouter()

# 回调路由 (不添加 /api/v1 前缀)
callback_router = APIRouter(tags=["华为云回调"])


# ==================== 设备管理 ====================
@router.post("/devices/register")
def register_device(request: DeviceRegisterRequest, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
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
    return {"message": "设备注册成功", "device_id": device.device_id}


@router.post("/devices/bind")
def bind_device(request: BindDeviceRequest, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """手动绑定设备到指定家庭。输入设备ID即可关联。"""
    existing = db.query(Device).filter(Device.device_id == request.device_id).first()
    if existing:
        if existing.family_id == request.family_id:
            return {"message": "设备已绑定到当前家庭", "device_id": existing.device_id, "family_id": existing.family_id}
        # 更新绑定到新家庭
        existing.family_id = request.family_id
        if request.name:
            existing.name = request.name
        db.commit()
        logger.info(f"设备 {request.device_id} 已重新绑定到家庭 {request.family_id}")
        return {"message": "设备已绑定到当前家庭", "device_id": existing.device_id, "family_id": existing.family_id}

    # 新设备，自动识别类型
    device_type = "env_monitor"
    if "light" in request.device_id.lower():
        device_type = "light"
    elif "motor" in request.device_id.lower() or "curtain" in request.device_id.lower():
        device_type = "curtain"

    device = Device(
        device_id=request.device_id,
        device_type=device_type,
        name=request.name or request.device_id,
        family_id=request.family_id,
        is_online=True,
        last_seen=datetime.now(timezone.utc),
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    logger.info(f"新设备绑定成功: {request.device_id} -> 家庭 {request.family_id}")
    return {"message": "设备绑定成功", "device_id": device.device_id, "family_id": device.family_id}


@router.get("/devices/query/{device_id}")
def query_device(device_id: str, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    return {
        "message": "设备查询成功",
        "device": {
            "device_id": device.device_id,
            "device_type": device.device_type,
            "name": device.name,
            "is_online": device.is_online,
            "last_seen": device.last_seen.isoformat() if device.last_seen else None,
        }
    }


@router.get("/devices/list", response_model=DeviceListResponse)
def list_devices(family_id: int = 1, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    # [DETECT:B1] 入口
    logger.info(f"[DETECT:B1] 设备列表查询入口 → family_id={family_id}, user_id={user_id}")
    devices = db.query(Device).filter(Device.family_id == family_id).all()

    # [DETECT:B2] 查询结果
    online_ids = [d.device_id for d in devices if d.is_online]
    offline_ids = [d.device_id for d in devices if not d.is_online]
    logger.info(
        f"[DETECT:B2] DB查询结果: family_id={family_id}, "
        f"总数={len(devices)}, 在线={len(online_ids)}, 离线={len(offline_ids)}, "
        f"在线ID={online_ids}, 离线ID={offline_ids}"
    )

    result = []
    for d in devices:
        result.append({
            "id": d.id,
            "device_id": d.device_id,
            "device_type": d.device_type,
            "name": d.name,
            "is_online": d.is_online,
            "last_seen": d.last_seen.isoformat() if d.last_seen else None,
        })

    # [DETECT:B3] 返回
    logger.info(f"[DETECT:B3] 设备列表返回: count={len(result)}, online_count={len(online_ids)}")
    return {"message": "设备列表查询成功", "count": len(result), "devices": result}


@router.post("/devices/init-huawei-device")
def init_huawei_device(family_id: int = 1, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    device_id = settings.HUAWEI_IOTDA_DEVICE_ID
    if not device_id:
        raise HTTPException(status_code=400, detail="未配置华为云设备ID")

    existing = db.query(Device).filter(Device.device_id == device_id).first()
    if existing:
        return {"message": "设备已存在", "device_id": device_id}

    device = Device(
        device_id=device_id,
        device_type="env_monitor",
        name="华为云环境监测器",
        family_id=family_id,
        is_online=True,
        last_seen=datetime.now(timezone.utc),
    )
    db.add(device)
    db.commit()
    logger.info(f"华为云设备初始化成功: {device_id}")
    return {"message": "华为云设备初始化成功", "device_id": device_id}


# ==================== 数据查询 ====================
@router.get("/data/latest/{device_id}", response_model=LatestDataResponse)
def get_latest_data(device_id: str, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
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
        "data": {
            "temperature": latest.sht30_temp_raw,
            "humidity": latest.sht30_humi_raw,
            "light": latest.bh1750_raw,
            "body_state": "有人" if latest.pir_gpio == 1 else "无人",
            "pir_gpio": latest.pir_gpio,
            "wifi_conn_state": latest.wifi_conn_state,
            "lightStatus": latest.lightStatus,
            "motorStatus": latest.motorStatus,
            "timestamp": latest.timestamp.isoformat() if latest.timestamp else None,
        }
    }


@router.get("/data/realtime/{device_id}")
def get_realtime_data(device_id: str, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """获取设备最新实时数据（完整9项），与APP层格式一致。"""
    latest = (
        db.query(EnvMonitorData)
        .filter(EnvMonitorData.device_id == device_id)
        .order_by(EnvMonitorData.timestamp.desc())
        .first()
    )

    device = db.query(Device).filter(Device.device_id == device_id).first()
    is_online = device.is_online if device else False

    if not latest:
        logger.warning(f"[DETECT:B9] /data/realtime: device={device_id} 无数据, is_online={is_online}")
        return {"message": "暂无数据", "online": is_online, "data": None}

    logger.info(f"[DETECT:B9] /data/realtime: device={device_id}, temp={latest.sht30_temp_raw}, humi={latest.sht30_humi_raw}, light={latest.bh1750_raw}")
    return {
        "message": "实时数据查询成功",
        "online": is_online,
        "data": build_realtime_data(latest),
    }


@router.get("/data/sync/{device_id}")
def sync_device_data(device_id: str, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    if not settings.HUAWEI_IOTDA_ENABLED:
        raise HTTPException(status_code=400, detail="华为云功能未启用")

    raw = iot_client.pull_device_data(device_id)
    if not raw.get("success"):
        error = raw.get("error", "同步失败")
        raise HTTPException(status_code=500, detail=error)

    data = raw.get("data", {})
    return {"message": "数据同步请求已发送", "data": data}


# ==================== 设备状态 ====================
@router.get("/devices/status/{device_id}", response_model=DeviceStatusResponse)
def get_device_status(device_id: str, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """查询设备最新状态（灯光开关、电机开关等），来自最近一次环境数据上报。"""
    latest = (
        db.query(EnvMonitorData)
        .filter(EnvMonitorData.device_id == device_id)
        .order_by(EnvMonitorData.timestamp.desc())
        .first()
    )
    if not latest:
        return DeviceStatusResponse(device_id=device_id)

    return DeviceStatusResponse(
        device_id=device_id,
        light_status=latest.lightStatus,
        motor_status=latest.motorStatus,
        temperature=latest.sht30_temp_raw,
        humidity=latest.sht30_humi_raw,
        timestamp=latest.timestamp.isoformat() if latest.timestamp else None,
    )


# ==================== 数据分析 ====================
@router.post("/data/validate")
def data_validate(request: DataValidateRequest, user_id: int = Depends(get_current_user_id)):
    """校验单条数据记录：入库前质量检查。"""
    result = validate_record(request.data)
    return {"message": "数据校验完成", "result": result}


@router.post("/data/quality")
def data_quality(
    request: Optional[DataQualityRequest] = Body(None),
    user_id: int = Depends(get_current_user_id),
):
    """数据质量报告：完整性、准确性、一致性 + 综合评分。"""
    params = request.dict() if request else {"device_id": None, "hours": 24}
    result = quality_report(**params)
    return {"message": "质量报告生成完成", "report": result}


@router.post("/data/stats/distribution")
def data_stats_distribution(
    request: Optional[DataStatsRequest] = Body(None),
    user_id: int = Depends(get_current_user_id),
):
    """字段分布统计：min/max/mean/median/std/异常值。"""
    params = {"device_id": None, "hours": 24}
    if request:
        params.update({k: v for k, v in request.dict().items() if k not in ("field", "interval")})
    result = distribution(**params)
    return {"message": "分布统计完成", "stats": result}


@router.post("/data/stats/correlation")
def data_stats_correlation(
    request: Optional[DataStatsRequest] = Body(None),
    user_id: int = Depends(get_current_user_id),
):
    """字段关联性分析：温度/湿度/光照 Pearson 相关系数。"""
    params = {"device_id": None, "hours": 24}
    if request:
        params.update({k: v for k, v in request.dict().items() if k in ("device_id", "hours")})
    result = correlation(**params)
    return {"message": "关联分析完成", "correlation": result}


@router.post("/data/stats/trends")
def data_stats_trends(
    request: Optional[DataStatsRequest] = Body(None),
    user_id: int = Depends(get_current_user_id),
):
    """时间序列趋势：按 interval 聚合 field 均值。"""
    params = {"device_id": None, "field": "sht30_temp_raw", "hours": 24, "interval": "hour"}
    if request:
        params.update(request.dict())
    result = trends(**params)
    return {"message": "趋势分析完成", "trends": result}


@router.post("/data/stats/frequency")
def data_stats_frequency(
    request: Optional[DataStatsRequest] = Body(None),
    user_id: int = Depends(get_current_user_id),
):
    """分类字段频次统计。"""
    params = {"device_id": None, "hours": 24}
    if request:
        params.update({k: v for k, v in request.dict().items() if k in ("device_id", "hours")})
    result = frequency_report(**params)
    return {"message": "频次统计完成", "frequency": result}


@router.post("/data/anomalies")
def data_anomalies(
    request: Optional[DataQualityRequest] = Body(None),
    user_id: int = Depends(get_current_user_id),
):
    """异常数据检测：IQR 方法。"""
    params = {"device_id": None, "hours": 24}
    if request:
        params.update({k: v for k, v in request.dict().items() if k in ("device_id", "hours")})
    result = detect_anomalies(**params)
    return {"message": "异常检测完成", "anomalies": result}


@router.get("/data/recommend")
def data_recommend(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """智能字段推荐：哪些字段需要关注。"""
    result = recommend_fields()
    return {"message": "字段推荐完成", "recommendations": result}


@router.post("/data/export")
def data_export(
    request: Optional[DataExportRequest] = Body(None),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """数据导出：JSON 或 CSV 格式。"""
    params = {"format": "json", "fields": None, "device_id": None, "hours": 24, "limit": 1000}
    if request:
        params.update(request.dict())

    cutoff = datetime.now(timezone.utc) - timedelta(hours=params["hours"])
    q = db.query(EnvMonitorData).filter(EnvMonitorData.timestamp >= cutoff)
    if params["device_id"]:
        q = q.filter(EnvMonitorData.device_id == params["device_id"])
    q = q.order_by(EnvMonitorData.timestamp.desc()).limit(params["limit"])

    # 解析需要导出的字段
    all_fields = [
        "id", "device_id", "family_id", "sht30_temp_raw", "sht30_humi_raw",
        "bh1750_raw", "mq2_adc", "pir_gpio", "wifi_rssi", "mpu_temp_raw",
        "lightStatus", "motorStatus", "wifi_conn_state", "timestamp",
    ]
    if params["fields"]:
        export_fields = [f.strip() for f in params["fields"].split(",") if f.strip() in all_fields]
    else:
        export_fields = all_fields

    rows = []
    for r in q.all():
        row = {}
        for f in export_fields:
            val = getattr(r, f, None)
            if isinstance(val, datetime):
                val = val.isoformat()
            row[f] = val
        rows.append(row)

    if params["format"] == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=export_fields)
        writer.writeheader()
        writer.writerows(rows)
        csv_str = output.getvalue()
        output.close()
        return {"message": "导出完成", "format": "csv", "count": len(rows), "data": csv_str}

    return {"message": "导出完成", "format": "json", "count": len(rows), "data": rows}


# ==================== 设备控制 ====================

def _send_command_and_log(command_name: str, paras: dict) -> dict:
    """发送命令到华为云IoTDA并记录完整诊断日志。"""
    logger.info(f"[CTRL:C3] IoTDA发送 → command={command_name}, paras={paras}, device={settings.HUAWEI_IOTDA_DEVICE_ID}")
    try:
        result = iot_client.send_command(command_name, paras)
        if result.get("success"):
            delivered = result.get("delivered", True)
            device_timeout = result.get("device_timeout", False)
            if device_timeout:
                logger.info(f"[CTRL:C4] 命令已下发华为云(设备响应超时) → {command_name} paras={paras}")
            else:
                logger.info(f"[CTRL:C4] 命令下发成功 → {command_name} paras={paras}, delivered={delivered}")
            return {"status": "success", "message": f"{command_name} 命令下发成功", "iotda_result": result}
        else:
            error = result.get("error", "未知错误")
            logger.error(f"[CTRL:C5] 命令下发失败 → {command_name} paras={paras}, error={error}")
            return {"status": "failed", "message": f"命令下发失败: {error}", "iotda_result": result}
    except Exception as e:
        logger.error(f"[CTRL:C5] 命令发送异常 → {command_name} paras={paras}, exception={e}")
        return {"status": "failed", "message": f"命令发送异常: {str(e)}"}


@router.post("/control/light", response_model=ControlResponse)
def control_light(request: ControlRequest, user_id: int = Depends(get_current_user_id)):
    val = request.onoff_value
    logger.info(f"[CTRL:C1] 灯光控制请求 → onoff={val}, user_id={user_id}")
    paras = {"onoff": val}
    if request.brightness is not None:
        paras["brightness"] = request.brightness
    logger.info(f"[CTRL:C2] 灯光控制参数构建 → command=light_control, paras={paras}")
    result = _send_command_and_log("light_control", paras)
    return {
        "message": result["message"],
        "status": result["status"],
        "command_name": "light_control",
        "paras": paras,
    }


@router.post("/control/motor", response_model=ControlResponse)
def control_motor(request: ControlRequest, user_id: int = Depends(get_current_user_id)):
    val = request.onoff_value
    logger.info(f"[CTRL:C1] 电机控制请求 → onoff={val}, user_id={user_id}")
    paras = {"onoff": val}
    if request.speed is not None:
        paras["speed"] = request.speed
    if request.direction is not None:
        paras["direction"] = request.direction
    logger.info(f"[CTRL:C2] 电机控制参数构建 → command=motor_control, paras={paras}")
    result = _send_command_and_log("motor_control", paras)
    return {
        "message": result["message"],
        "status": result["status"],
        "command_name": "motor_control",
        "paras": paras,
    }


@router.post("/control/beep", response_model=ControlResponse)
def control_beep(request: ControlRequest, user_id: int = Depends(get_current_user_id)):
    logger.info(f"[CTRL:C1] 蜂鸣器控制请求 → user_id={user_id}")
    paras = {}
    if request.duration is not None:
        paras["duration"] = request.duration
    if request.frequency is not None:
        paras["frequency"] = request.frequency
    logger.info(f"[CTRL:C2] 蜂鸣器控制参数构建 → command=beep_play, paras={paras}")
    result = _send_command_and_log("beep_play", paras)
    return {
        "message": result["message"],
        "status": result["status"],
        "command_name": "beep_play",
        "paras": paras,
    }


@router.post("/control/beep_song", response_model=ControlResponse)
def control_beep_song(request: BeepSongRequest, user_id: int = Depends(get_current_user_id)):
    logger.info(f"[CTRL:C1] 蜂鸣器歌曲控制请求 → id={request.id}, user_id={user_id}")
    paras = {"id": request.id}
    logger.info(f"[CTRL:C2] 蜂鸣器歌曲参数构建 → command=beep_song, paras={paras}")
    result = _send_command_and_log("beep_song", paras)
    return {
        "message": result["message"],
        "status": result["status"],
        "command_name": "beep_song",
        "paras": paras,
    }


@router.post("/control/beep_stop", response_model=ControlResponse)
def control_beep_stop(user_id: int = Depends(get_current_user_id)):
    logger.info(f"[CTRL:C1] 蜂鸣器停止请求 → user_id={user_id}")
    result = _send_command_and_log("beep_stop", {})
    return {
        "message": result["message"],
        "status": result["status"],
        "command_name": "beep_stop",
        "paras": {},
    }


# ========== 快捷模式（睡眠/阅读） ==========
@router.post("/control/mode", response_model=ControlResponse)
def control_mode(request: ModeRequest, user_id: int = Depends(get_current_user_id)):
    mode_name = "早间提神模式" if request.mode == "morning" else "阅读模式"
    logger.info(f"[MODE:C1] ========== {mode_name}激活开始 → user_id={user_id} ==========")

    results = []
    all_success = True

    if request.mode == "morning":
        # 早间提神模式: 灯光 ON+STATIC+绿色 → 播放歌曲id=1
        logger.info(f"[MODE:C2] 早间提神模式 - 合并灯光命令: ON + 常亮 + 绿色")
        r1 = _send_command_and_log("light_control", {"onoff": "ON", "mode": "STATIC", "color": "GREEN"})
        results.append(("灯光(ON+常亮+绿色)", r1))
        if r1["status"] != "success":
            all_success = False

        logger.info(f"[MODE:C3] 早间提神模式 - 播放歌曲 id=1 (熙熙攘攘我们的城市)")
        r2 = _send_command_and_log("beep_song", {"id": 1})
        results.append(("歌曲id=1", r2))
        if r2["status"] != "success":
            all_success = False

        logger.info(f"[MODE:C4] 早间提神模式 - 激活蜂鸣器播放")
        r3 = _send_command_and_log("beep_play", {})
        results.append(("激活蜂鸣器", r3))
        if r3["status"] != "success":
            all_success = False

    else:  # read
        # 阅读模式: 灯光二合一(ON+BREATH) → 播放歌曲id=2
        logger.info(f"[MODE:C2] 阅读模式 - 合并灯光命令: ON + 呼吸灯")
        r1 = _send_command_and_log("light_control", {"onoff": "ON", "mode": "BREATH"})
        results.append(("灯光(ON+呼吸灯)", r1))
        if r1["status"] != "success":
            all_success = False

        logger.info(f"[MODE:C3] 阅读模式 - 播放歌曲 id=2 (春日影)")
        r2 = _send_command_and_log("beep_song", {"id": 2})
        results.append(("歌曲id=2", r2))
        if r2["status"] != "success":
            all_success = False

        logger.info(f"[MODE:C4] 阅读模式 - 激活蜂鸣器播放")
        r3 = _send_command_and_log("beep_play", {})
        results.append(("激活蜂鸣器", r3))
        if r3["status"] != "success":
            all_success = False

    status = "success" if all_success else "partial"
    logger.info(f"[MODE:C6] ========== {mode_name}激活完成 → status={status} ==========")
    return {
        "message": f"{mode_name}激活{'成功' if all_success else '部分成功'}",
        "status": status,
        "command_name": "mode",
        "paras": {"mode": request.mode, "results": results},
    }


# ========== 重置所有设备 ==========
@router.post("/control/reset", response_model=ControlResponse)
def control_reset(user_id: int = Depends(get_current_user_id)):
    logger.info(f"[RESET:C1] ========== 重置所有设备开始 → user_id={user_id} ==========")

    results = []
    all_success = True

    logger.info(f"[RESET:C2] 重置 - 步骤1: 关闭灯光")
    r1 = _send_command_and_log("light_control", {"onoff": "OFF"})
    results.append(("灯光关闭", r1))
    if r1["status"] != "success":
        all_success = False

    logger.info(f"[RESET:C3] 重置 - 步骤2: 停止蜂鸣器")
    r2 = _send_command_and_log("beep_stop", {})
    results.append(("蜂鸣器停止", r2))
    if r2["status"] != "success":
        all_success = False

    logger.info(f"[RESET:C3.1] 重置 - 步骤2.5: 切回默认歌曲 id=0 (两只老虎)")
    r2b = _send_command_and_log("beep_song", {"id": 0})
    results.append(("歌曲重置id=0", r2b))
    if r2b["status"] != "success":
        all_success = False

    logger.info(f"[RESET:C4] 重置 - 步骤3: 关闭电机")
    r3 = _send_command_and_log("motor_control", {"onoff": "OFF"})
    results.append(("电机关闭", r3))
    if r3["status"] != "success":
        all_success = False

    status = "success" if all_success else "partial"
    logger.info(f"[RESET:C5] ========== 重置完成 → status={status} ==========")
    return {
        "message": f"重置{'成功' if all_success else '部分成功'}",
        "status": status,
        "command_name": "reset",
        "paras": {"results": results},
    }


@router.post("/control/light/color", response_model=ControlResponse)
def control_light_color(request: LightColorRequest, user_id: int = Depends(get_current_user_id)):
    logger.info(f"[CTRL:C1] 灯光颜色控制请求 → color={request.color}, user_id={user_id}")
    paras = {"color": color_to_int(request.color)}
    result = _send_command_and_log("light_control", paras)
    return {
        "message": result["message"],
        "status": result["status"],
        "command_name": "light_control",
        "paras": paras,
    }


@router.post("/control/light/brightness", response_model=ControlResponse)
def control_light_brightness(request: LightBrightnessRequest, user_id: int = Depends(get_current_user_id)):
    logger.info(f"[CTRL:C1] 灯光亮度控制请求 → brightness={request.brightness}, user_id={user_id}")
    paras = {"brightness": request.brightness}
    result = _send_command_and_log("light_control", paras)
    return {
        "message": result["message"],
        "status": result["status"],
        "command_name": "light_control",
        "paras": paras,
    }


@router.post("/control/light/mode", response_model=ControlResponse)
def control_light_mode(request: LightModeRequest, user_id: int = Depends(get_current_user_id)):
    logger.info(f"[CTRL:C1] 灯光模式控制请求 → mode={request.mode}, user_id={user_id}")
    paras = {"mode": request.mode}
    result = _send_command_and_log("light_control", paras)
    return {
        "message": result["message"],
        "status": result["status"],
        "command_name": "light_control",
        "paras": paras,
    }


@router.post("/control/motor/speed", response_model=ControlResponse)
def control_motor_speed(request: MotorSpeedRequest, user_id: int = Depends(get_current_user_id)):
    logger.info(f"[CTRL:C1] 电机速度控制请求 → speed={request.speed}, user_id={user_id}")
    paras = {"speed": request.speed}
    result = _send_command_and_log("motor_control", paras)
    return {
        "message": result["message"],
        "status": result["status"],
        "command_name": "motor_control",
        "paras": paras,
    }


# ==================== 数据分析 API ====================
analysis_router = APIRouter()


@analysis_router.get("/analysis/realtime")
def get_analysis_realtime(db: Session = Depends(get_db)):
    """返回当前实时环境数据 + 最新 AI 预测（供分析看板首页卡片使用）。"""
    latest_env = (
        db.query(EnvMonitorData)
        .order_by(EnvMonitorData.timestamp.desc())
        .first()
    )
    latest_pred = (
        db.query(AIPrediction)
        .order_by(AIPrediction.predict_time.desc())
        .first()
    )

    result = {
        "temperature": None,
        "humidity": None,
        "light": None,
        "smoke": None,
        "pir_detected": None,
        "wifi_connected": None,
        "lightStatus": None,
        "motorStatus": None,
        "scene": None,
        "activity_index": None,
        "night_zscore": None,
        "timestamp": None,
    }

    if latest_env:
        result.update({
            "temperature": latest_env.sht30_temp_raw,
            "humidity": latest_env.sht30_humi_raw,
            "light": latest_env.bh1750_raw,
            "smoke": latest_env.mq2_adc,
            "pir_detected": latest_env.pir_gpio == 1 if latest_env.pir_gpio is not None else None,
            "wifi_connected": latest_env.wifi_conn_state == 1 if latest_env.wifi_conn_state is not None else None,
            "lightStatus": (latest_env.lightStatus or "").upper() == "ON",
            "motorStatus": (latest_env.motorStatus or "").upper() == "ON",
            "timestamp": latest_env.timestamp.isoformat() if latest_env.timestamp else None,
        })

    if latest_pred:
        result.update({
            "scene": latest_pred.scene,
            "activity_index": latest_pred.activity_index,
            "night_zscore": latest_pred.night_zscore,
        })

    return {"code": 200, "data": result}


@analysis_router.get("/analysis/night-anomaly")
def get_night_anomaly_data(
    days: int = 3,
    db: Session = Depends(get_db),
):
    """返回夜间异常数据：motion z-score 时间线、异常点列表、每日汇总。
    数据源：ai_predictions 表 + env_monitor_data 表。
    """
    from datetime import timedelta
    since = datetime.now(timezone.utc) - timedelta(days=days)

    preds = (
        db.query(AIPrediction)
        .filter(AIPrediction.predict_time >= since)
        .order_by(AIPrediction.predict_time.asc())
        .all()
    )

    # 同时取对应的环境数据
    env_records = (
        db.query(EnvMonitorData)
        .filter(EnvMonitorData.timestamp >= since)
        .order_by(EnvMonitorData.timestamp.asc())
        .all()
    )

    env_map = {}
    for e in env_records:
        if e.timestamp:
            minute_key = e.timestamp.replace(second=0, microsecond=0)
            env_map[minute_key] = {
                "sht30_temp_raw": e.sht30_temp_raw,
                "sht30_humi_raw": e.sht30_humi_raw,
                "bh1750_raw": e.bh1750_raw,
                "pir_gpio": e.pir_gpio,
            }

    points = []
    for p in preds:
        hour = p.predict_time.hour if p.predict_time else 0
        is_night = hour >= 22 or hour < 6
        t = p.predict_time
        minute_key = t.replace(second=0, microsecond=0) if t else None
        env = env_map.get(minute_key, {}) if minute_key else {}

        points.append({
            "timestamp": t.isoformat() if t else None,
            "date": t.strftime("%Y-%m-%d") if t else None,
            "hour": hour,
            "minute_of_day": hour * 60 + (t.minute if t else 0),
            "is_night": 1 if is_night else 0,
            "pir_gpio": env.get("pir_gpio"),
            "motion_5min_sum": float(p.motion_30min_sum / 6) if p.motion_30min_sum else 0,
            "motion_30min_sum": float(p.motion_30min_sum or 0),
            "activity_index": float(p.activity_index or 0),
            "activity_10min_mean": float(p.activity_index or 0) * 0.8,
            "temp_comfort": 1,
            "humi_comfort": 1,
            "env_discomfort": float(p.env_discomfort or 0),
            "motion_zscore": float(p.night_zscore or 0),
            "is_anomaly_point": 1 if p.is_night_anomalous else 0,
            "sht30_temp_raw": env.get("sht30_temp_raw"),
        })

    # 每日汇总
    daily = {}
    for pt in points:
        d = pt["date"]
        if d not in daily:
            daily[d] = {"count": 0, "max_zscore": 0.0}
        if pt["is_anomaly_point"]:
            daily[d]["count"] += 1
        if pt["motion_zscore"] > daily[d]["max_zscore"]:
            daily[d]["max_zscore"] = pt["motion_zscore"]

    daily_summary = [
        {
            "date": d,
            "anomaly_count": info["count"],
            "max_zscore": round(info["max_zscore"], 2),
            "is_anomalous": info["count"] > 0,
        }
        for d, info in sorted(daily.items(), reverse=True)[:7]
    ]

    return {"code": 200, "data": {"points": points, "daily_summary": daily_summary}}


@analysis_router.get("/analysis/timeseries")
def get_analysis_timeseries(
    days: int = 7,
    db: Session = Depends(get_db),
):
    """返回环境时序数据 + 场景 + 睡眠特征（供分析看板图表使用）。"""
    from datetime import timedelta
    since = datetime.now(timezone.utc) - timedelta(days=days)

    env_records = (
        db.query(EnvMonitorData)
        .filter(EnvMonitorData.timestamp >= since)
        .order_by(EnvMonitorData.timestamp.asc())
        .all()
    )

    ai_records = (
        db.query(AIPrediction)
        .filter(AIPrediction.predict_time >= since)
        .order_by(AIPrediction.predict_time.asc())
        .all()
    )

    # 环境数据
    full_data = []
    for e in env_records:
        full_data.append({
            "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            "temperature": e.sht30_temp_raw,
            "humidity": e.sht30_humi_raw,
            "combustible_gas": e.mq2_adc,
            "motion_detected": e.pir_gpio,
            "occupied_probability": 0.5,
            "predicted_occupied": 1 if e.pir_gpio == 1 else 0,
        })

    # 睡眠特征（从 AI 预测推导）
    sleep_data = []
    for a in ai_records:
        hour = a.predict_time.hour if a.predict_time else 0
        sleep_data.append({
            "timestamp": a.predict_time.isoformat() if a.predict_time else None,
            "date": a.predict_time.strftime("%Y-%m-%d") if a.predict_time else None,
            "hour": hour,
            "motion_5min_sum": float(a.motion_30min_sum / 6) if a.motion_30min_sum else 0,
            "activity_index": float(a.activity_index or 0),
            "first_motion": None,
            "last_motion": None,
            "sleep_start": None,
            "sleep_end": None,
        })

    # 场景数据（从 AI 预测推导）
    scene_data = []
    for a in ai_records:
        scene_data.append({
            "timestamp": a.predict_time.isoformat() if a.predict_time else None,
            "scene": a.scene,
            "light_status_num": 1 if a.light_current_state else 0,
            "motor_status_num": 0,
            "light_changed": 1 if a.light_will_change else 0,
            "bh1750_raw": float(a.env_discomfort or 0) * 100,
        })

    return {
        "code": 200,
        "data": {
            "full_data": full_data,
            "sleep_data": sleep_data,
            "scene_data": scene_data,
        },
    }


# ==================== 华为云回调 ====================
def _run_ai_prediction(db: Session, device_id: str):
    """在数据入库后运行四模型预测 + 写入 ai_predictions 表。"""
    try:
        import sys as _s, os as _o
        _ai = _o.path.abspath(_o.path.join(_o.path.dirname(__file__), '..', '..', 'ai', 'src'))
        if _ai not in _s.path:
            _s.path.insert(0, _ai)
        from ai_service import predictor, compute_features

        features = compute_features(db, device_id)
        if not features:
            return None
        if not predictor.is_loaded:
            logger.warning("[AI预测] 模型未加载，跳过")
            return None

        ai_result = predictor.predict_all(features)
        night = ai_result.get("night_anomaly", {})

        rec = AIPrediction(
            family_id=1,
            device_id=device_id,
            # 任务1
            is_night_anomalous=night.get("is_anomalous", False),
            night_zscore=night.get("zscore", 0.0),
            night_current_motion=night.get("current_motion_5min", 0.0),
            night_baseline_mean=night.get("baseline_mean", 0.0),
            night_baseline_std=night.get("baseline_std", 0.0),
            night_is_nighttime=night.get("is_nighttime", False),
            # 任务2
            activity_index=ai_result.get("activity"),
            accel_magnitude=ai_result.get("accel_magnitude", 0.0),
            gyro_magnitude=ai_result.get("gyro_magnitude", 0.0),
            env_discomfort=ai_result.get("env_discomfort", 0.0),
            # 任务3
            scene=ai_result.get("scene"),
            scene_probability=ai_result.get("scene_probability", 0.0),
            scene_prob_sleep=ai_result.get("scene_prob_sleep", 0.0),
            scene_prob_away=ai_result.get("scene_prob_away", 0.0),
            scene_prob_indoor=ai_result.get("scene_prob_indoor", 0.0),
            scene_prob_other=ai_result.get("scene_prob_other", 0.0),
            scene_second=ai_result.get("scene_second"),
            # 任务4
            light_will_change=ai_result.get("light_will_change", False),
            light_change_probability=ai_result.get("light_change_probability", 0.0),
            light_nochange_probability=ai_result.get("light_nochange_probability", 0.0),
            light_current_state=ai_result.get("light_current_state", False),
            # 通用
            motion_30min_sum=ai_result.get("motion_30min_sum", 0.0),
            motion_1h_sum=ai_result.get("motion_1h_sum", 0.0),
            no_motion_duration_min=ai_result.get("no_motion_duration_min", 0.0),
            time_since_last_light_change=ai_result.get("time_since_last_light_change", 0.0),
        )
        db.add(rec)
        db.commit()
        logger.info(f"[AI预测] 入库: scene={rec.scene}, activity={rec.activity_index}")
        return ai_result
    except Exception as e:
        logger.error(f"[AI预测] 失败: {e}")
        return None


def _push_to_gateway(device_id: str, body: dict):
    """通过网关服务的 /broadcast 接口将最新数据推送到前端。"""
    try:
        res = http_requests.post(
            "http://localhost:8010/broadcast",
            json={
                "type": "device_update",
                "device_id": device_id,
                "family_id": "1",
                "data": body,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            timeout=3,
        )
        if res.status_code == 200:
            logger.info(f"广播成功: device={device_id}")
        else:
            logger.warning(f"广播失败: HTTP {res.status_code}, device={device_id}")
    except Exception as e:
        logger.debug(f"广播异常(网关可能未启动): device={device_id}, err={e}")


@callback_router.post("/api/v1/devices/huawei-callback")
async def huawei_callback(request: Request, db: Session = Depends(get_db)):
    try:
        notify_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="无效的JSON")

    # 华为云标准格式: 外层有 notify_data 包装
    payload = notify_data.get("notify_data", notify_data)
    body = parse_huawei_callback_data(payload)
    device_id = (payload.get("header", {}).get("device_id")
                 or notify_data.get("device_id")
                 or settings.HUAWEI_IOTDA_DEVICE_ID)

    logger.info(f"收到回调: device={device_id}")

    store_env_data(db, device_id, body, notify_data)
    _push_to_gateway(device_id, body)

    # AI 预测
    _run_ai_prediction(db, device_id)

    return {"status": "success", "message": "数据已接收"}


@callback_router.post("/")
async def root_callback(request: Request, db: Session = Depends(get_db)):
    body = await request.body()
    logger.info(f"收到根路径回调，body长度: {len(body)}")
    try:
        notify_data = json.loads(body)
        device_id = notify_data.get("device_id") or settings.HUAWEI_IOTDA_DEVICE_ID
        parsed = parse_huawei_callback_data(notify_data)
        store_env_data(db, device_id, parsed, notify_data)
        _push_to_gateway(device_id, parsed)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"处理根回调失败: {e}")
        return {"status": "error", "message": str(e)}
