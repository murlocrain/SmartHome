from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict
from datetime import datetime, timezone
import logging

from common.database import get_db
from common.models import SceneRule, SceneEventLog, EnvMonitorData
from common.schemas.common import ResponseModel
from common.config import settings
from common.security import get_current_user_id
from .schemas import (
    SceneRuleCreate, SceneRuleResponse, SceneEventLogResponse,
    SceneEvent, RoomStateResponse,
    AIChatRequest, AIChatResponse, AIAgentRequest, AIAgentResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()

room_states: Dict[int, dict] = {}
scene_connections: Dict[str, set] = {}


def _get_latest_env_data(db: Session, family_id: int):
    return (
        db.query(EnvMonitorData)
        .filter(EnvMonitorData.family_id == family_id)
        .order_by(EnvMonitorData.timestamp.desc())
        .first()
    )


# ==================== 场景 WebSocket ====================
@router.websocket("/scenes/ws/{family_id}")
async def scene_websocket_endpoint(websocket: WebSocket, family_id: str, token: str = Query(None)):
    """场景服务 WebSocket：需携带 token 进行认证。"""
    from common.security import decode_token
    if not token:
        await websocket.close(code=4001, reason="缺少认证令牌")
        return
    payload = decode_token(token)
    if not payload:
        await websocket.close(code=4001, reason="无效的令牌或令牌已过期")
        return
    await websocket.accept()
    key = f"scene_{family_id}"
    if key not in scene_connections:
        scene_connections[key] = set()
    scene_connections[key].add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if key in scene_connections:
            scene_connections[key].discard(websocket)


# ==================== 场景评估 ====================
@router.post("/scenes/trigger/{family_id}")
async def trigger_scene_evaluation(family_id: int, data: dict, user_id: int = Depends(get_current_user_id)):
    from common.database import SessionLocal
    db = SessionLocal()
    try:
        room_states[family_id] = data
        latest = _get_latest_env_data(db, family_id)
        scenes = _evaluate_scenes(family_id, data, latest, db)

        if scenes:
            key = f"scene_{family_id}"
            if key in scene_connections:
                for ws in list(scene_connections[key]):
                    try:
                        await ws.send_json({
                            "type": "scene_event",
                            "family_id": family_id,
                            "scenes": [s for s in scenes]
                        })
                    except Exception:
                        scene_connections[key].discard(ws)
    finally:
        db.close()
    return {"message": "Scene evaluation triggered", "scenes": scenes}


@router.get("/scenes/state/{family_id}", response_model=ResponseModel[RoomStateResponse])
def get_room_state(family_id: int, user_id: int = Depends(get_current_user_id)):
    from common.database import SessionLocal
    db = SessionLocal()
    try:
        latest = _get_latest_env_data(db, family_id)
        if not latest:
            return ResponseModel(data=RoomStateResponse(
                family_id=family_id, temperature=None, humidity=None,
                illumination=None, has_person=False, smoke_detected=False,
                wifi_connected=True, last_update=None,
            ))

        try:
            temp = float(latest.sht30_temp_raw) if latest.sht30_temp_raw is not None else None
        except (ValueError, TypeError):
            temp = None
        try:
            humi = float(latest.sht30_humi_raw) if latest.sht30_humi_raw is not None else None
        except (ValueError, TypeError):
            humi = None

        has_person = latest.pir_gpio == 1 if latest.pir_gpio is not None else False
        wifi_connected = latest.wifi_conn_state == 1 if latest.wifi_conn_state is not None else False

        return ResponseModel(data=RoomStateResponse(
            family_id=family_id, temperature=temp, humidity=humi,
            illumination=latest.bh1750_raw, has_person=has_person,
            smoke_detected=False, wifi_connected=wifi_connected,
            last_update=latest.timestamp.isoformat() if latest.timestamp else None,
        ))
    finally:
        db.close()


# ==================== 场景规则 CRUD ====================
@router.post("/scenes/rules", response_model=SceneRuleResponse)
def create_scene_rule(rule: SceneRuleCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    scene_rule = SceneRule(
        family_id=rule.family_id, name=rule.name, scene_id=rule.scene_id,
        conditions=rule.conditions, actions=rule.actions,
    )
    db.add(scene_rule)
    db.commit()
    db.refresh(scene_rule)
    return SceneRuleResponse.model_validate(scene_rule)


@router.get("/scenes/rules/{family_id}", response_model=List[SceneRuleResponse])
def get_family_rules(family_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    rules = db.query(SceneRule).filter(SceneRule.family_id == family_id).all()
    return [SceneRuleResponse.model_validate(r) for r in rules]


@router.put("/scenes/rules/{rule_id}")
def update_scene_rule(rule_id: int, updates: dict, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    rule = db.query(SceneRule).filter(SceneRule.id == rule_id).first()
    if not rule:
        return {"success": False}
    for key, value in updates.items():
        setattr(rule, key, value)
    db.commit()
    return {"success": True}


@router.delete("/scenes/rules/{rule_id}")
def delete_scene_rule(rule_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    rule = db.query(SceneRule).filter(SceneRule.id == rule_id).first()
    if not rule:
        return {"success": False}
    db.delete(rule)
    db.commit()
    return {"success": True}


@router.get("/scenes/events/{family_id}", response_model=List[SceneEventLogResponse])
def get_scene_events(family_id: int, hours: int = 24, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    from datetime import timedelta
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    logs = (
        db.query(SceneEventLog)
        .filter(SceneEventLog.family_id == family_id, SceneEventLog.created_at >= since)
        .order_by(SceneEventLog.created_at.desc())
        .all()
    )
    return [SceneEventLogResponse.model_validate(log) for log in logs]


# ==================== AI 智能体 ====================
@router.post("/ai/chat", response_model=AIChatResponse)
def ai_chat(request: AIChatRequest):
    import sys as _s, os as _o
    _ai = _o.path.abspath(_o.path.join(_o.path.dirname(__file__), '..', '..', 'ai', 'src'))
    if _ai not in _s.path:
        _s.path.insert(0, _ai)
    from agent_service.ai_client import chat_with_ai
    message = request.message
    reply = chat_with_ai(message)
    return {"message": message, "reply": reply, "model": settings.AI_MODEL}


@router.post("/ai/agent", response_model=AIAgentResponse)
def ai_agent(request: AIAgentRequest, db: Session = Depends(get_db)):
    import sys as _s, os as _o
    _ai = _o.path.abspath(_o.path.join(_o.path.dirname(__file__), '..', '..', 'ai', 'src'))
    if _ai not in _s.path:
        _s.path.insert(0, _ai)
    from agent_service.ai_client import smart_agent
    result = smart_agent(request.message, db)
    return result


# ==================== 内置场景评估逻辑 ====================
def _evaluate_scenes(family_id: int, state: dict, latest_data, db: Session) -> List[dict]:
    scenes = []
    try:
        temp = float(state.get("temperature", 0))
    except (ValueError, TypeError):
        temp = 0
    try:
        humi = float(state.get("humidity", 0))
    except (ValueError, TypeError):
        humi = 0
    try:
        light = float(state.get("illumination", 0))
    except (ValueError, TypeError):
        light = 0

    has_person = state.get("body_state", "") in ("present", "detected", "1", "有人")

    if has_person:
        scenes.append({
            "scene_id": "presence_detection", "name": "人体检测",
            "description": "检测到有人活动", "suggestion": "欢迎回家！", "priority": "info"
        })

    if temp > 30:
        scenes.append({
            "scene_id": "temp_high", "name": "温度过高",
            "description": f"当前温度: {temp}°C", "suggestion": "建议开启空调或开窗通风", "priority": "warning"
        })

    return scenes
