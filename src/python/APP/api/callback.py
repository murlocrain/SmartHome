import sys as _sys
import os as _os
_AI_SRC = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..', '..', '..', 'ai', 'src'))
if _AI_SRC not in _sys.path:
    _sys.path.insert(0, _AI_SRC)

import json
from datetime import datetime, timezone
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session

from common.config import settings, logger
from common.database import get_db
from common.device_payloads import build_realtime_data
from common.huawei_callback import parse_huawei_callback_data, store_env_data
from common.models import EnvMonitorData
from common.models import AIPrediction
from common.websocket_manager import manager as ws_manager
from ai_service import predictor, compute_features

router = APIRouter(tags=["华为云回调"])


def _safe_float(val):
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _safe_int(val):
    if val is None:
        return None
    try:
        if isinstance(val, dict):
            return int(val.get("lux") or val.get("value") or 0)
        return int(val)
    except (TypeError, ValueError):
        return None


def _bool_to_onoff(val):
    if val is None:
        return None
    if isinstance(val, bool):
        return "ON" if val else "OFF"
    s = str(val).upper()
    if s in ("1", "TRUE", "ON"):
        return "ON"
    if s in ("0", "FALSE", "OFF"):
        return "OFF"
    return s


def _build_frontend_data(data: EnvMonitorData) -> dict:
    """将数据库记录转换为前端需要的9项实时数据格式。"""
    return build_realtime_data(data)


async def _broadcast_to_frontend(device_id: str, data: EnvMonitorData, ai_result: dict = None):
    """WebSocket 广播完整实时数据，包含 AI 预测结果。"""
    payload = _build_frontend_data(data)
    if ai_result:
        payload["ai"] = ai_result
    await ws_manager.broadcast({
        "type": "device_update",
        "device_id": device_id,
        "data": payload,
    })
    logger.info(f"[DETECT:A3] WebSocket广播完成: device={device_id}, clients_connected={len(getattr(ws_manager, '_connections', []))}")


def _store_ai_prediction(db: Session, device_id: str, ai_result: dict):
    """将 AI 预测结果写入 ai_predictions 表。"""
    rec = AIPrediction(
        family_id=1,
        device_id=device_id,
        activity_index=ai_result.get("activity"),
        scene=ai_result.get("scene"),
        scene_probability=ai_result.get("scene_probability"),
        light_will_change=ai_result.get("light_will_change"),
        light_change_probability=ai_result.get("light_change_probability"),
        is_night_anomalous=ai_result.get("night_anomaly", {}).get("is_anomalous", False),
        night_zscore=ai_result.get("night_anomaly", {}).get("zscore", 0.0),
        night_current_motion=ai_result.get("night_anomaly", {}).get("current_motion_5min", 0.0),
    )
    db.add(rec)
    db.commit()
    logger.info(f"AI预测结果入库: device={device_id}, scene={rec.scene}, activity={rec.activity_index}")


@router.post("/api/v1/devices/huawei-callback")
async def huawei_callback(request: Request, db: Session = Depends(get_db)):
    logger.info(f"[DETECT:A4] 收到华为云回调 → IP={request.client.host if request.client else 'unknown'}")

    body = await request.body()
    try:
        payload = json.loads(body.decode("utf-8"))
        logger.info(f"[DETECT:A4] 回调原始数据(前500字符): {json.dumps(payload, ensure_ascii=False)[:500]}")
    except Exception as e:
        logger.error(f"[DETECT:A4] 回调JSON解析失败: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON")

    notify_data = payload.get("notify_data", {})
    header = notify_data.get("header", {})
    device_id = header.get("device_id", settings.HUAWEI_IOTDA_DEVICE_ID)

    parsed_body = parse_huawei_callback_data(notify_data)
    logger.info(f"[DETECT:A5] 回调解析完成: device={device_id}, body字段数={len(parsed_body)}, keys={list(parsed_body.keys())[:10]}")

    try:
        store_env_data(db, device_id, parsed_body, payload)
    except Exception as e:
        logger.error(f"[DETECT:A5] 存储环境数据失败: {e}")

    # AI 预测
    ai_result = None
    try:
        features = compute_features(db, device_id)
        if features and predictor.is_loaded:
            ai_result = predictor.predict_all(features)
            _store_ai_prediction(db, device_id, ai_result)
    except Exception as e:
        logger.error(f"AI 预测失败: {e}")

    # 查询刚插入的最新记录用于广播
    try:
        latest = (
            db.query(EnvMonitorData)
            .filter(EnvMonitorData.device_id == device_id)
            .order_by(EnvMonitorData.timestamp.desc())
            .first()
        )
        if latest:
            await _broadcast_to_frontend(device_id, latest, ai_result)
    except Exception as e:
        logger.error(f"WebSocket 广播失败: {e}")

    return {"status": "success", "message": "Callback received"}


@router.post("/")
async def root_callback(request: Request, db: Session = Depends(get_db)):
    body = await request.body()
    try:
        payload = json.loads(body.decode("utf-8"))
        logger.info(f"收到根路径回调: {json.dumps(payload, ensure_ascii=False)[:200]}")
    except Exception:
        pass
    return {"status": "ok"}
