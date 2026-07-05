import sys as _sys
import os as _os
_AI_SRC = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..', '..', '..', 'ai', 'src'))
if _AI_SRC not in _sys.path:
    _sys.path.insert(0, _AI_SRC)

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from common.config import settings, logger
from common.database import get_db
from common.models import EnvMonitorData
from common.models import AIPrediction
from agent_service.ai_client import chat_with_ai, smart_agent, analyze_environment, build_agent_context
from APP.schemas import AIChatRequest, AIChatResponse, AIAgentRequest, AIAgentResponse

router = APIRouter(prefix="/ai", tags=["AI 智能体"])


# ==================== 1. 简单对话（不控制设备，只聊天/问答） ====================
@router.post("/chat", response_model=AIChatResponse)
def ai_chat(request: AIChatRequest, db: Session = Depends(get_db)):
    """和 AI 随便聊天，自动注入当前环境和预测上下文。"""
    message = request.message
    logger.info(f"[AI对话] 用户: {message}")

    # 构造三层上下文
    context = _build_full_context(db)
    reply = chat_with_ai(message, extra_context=context)
    logger.info(f"[AI对话] AI: {reply}")
    return {"message": message, "reply": reply, "model": settings.AI_MODEL}


# ==================== 2. 智能体：自然语言控制设备（一句话打开灯/风扇） ====================
@router.post("/agent", response_model=AIAgentResponse)
def ai_agent(request: AIAgentRequest, db: Session = Depends(get_db)):
    """智能体核心接口：一句话控制设备 + 获取环境建议 + AI预测解读。"""
    message = request.message
    logger.info(f"[AI智能体] 用户: {message}")

    latest = (
        db.query(EnvMonitorData)
        .order_by(EnvMonitorData.timestamp.desc())
        .first()
    )
    env_data = None
    if latest:
        env_data = {
            "temperature": latest.sht30_temp_raw,
            "humidity": latest.sht30_humi_raw,
            "light": latest.bh1750_raw,
            "body_state": "有人" if latest.pir_gpio == 1 else "无人",
            "timestamp": str(latest.timestamp),
            "lightStatus": (latest.lightStatus or "").upper() == "ON",
            "motorStatus": (latest.motorStatus or "").upper() == "ON",
        }

    # 查询最新 AI 预测
    ai_prediction = _get_latest_prediction(db)

    result = smart_agent(message, env_data, ai_prediction)
    logger.info(f"[AI智能体] 意图={result.get('intent')}, 目标={result.get('target')}, 动作={result.get('action')}")
    logger.info(f"[AI智能体] AI回复: {result.get('ai_reply')}")

    return {
        "message": message,
        "reply": result["ai_reply"],
        "parsed": {
            "intent": result["intent"],
            "target": result["target"],
            "action": result["action"],
        },
        "device_result": result["device_result"],
        "current_env": env_data,
        "env_suggestion": result["env_suggestion"],
        "ai_prediction": ai_prediction,
    }


# ==================== 3. 环境分析：基于最新传感器数据+AI预测给建议 ====================
@router.post("/analyze-env")
def ai_analyze_env(db: Session = Depends(get_db)):
    """让 AI 分析当前环境数据和预测结果并给出建议。不需要传参数。"""
    latest = (
        db.query(EnvMonitorData)
        .order_by(EnvMonitorData.timestamp.desc())
        .first()
    )

    env_data = None
    if latest:
        env_data = {
            "temperature": latest.sht30_temp_raw,
            "humidity": latest.sht30_humi_raw,
            "light": latest.bh1750_raw,
            "body_state": "有人" if latest.pir_gpio == 1 else "无人",
            "timestamp": str(latest.timestamp),
            "lightStatus": (latest.lightStatus or "").upper() == "ON",
            "motorStatus": (latest.motorStatus or "").upper() == "ON",
        }

    ai_prediction = _get_latest_prediction(db)
    suggestion = analyze_environment(env_data, ai_prediction)

    return {
        "current_env": env_data,
        "suggestion": suggestion,
        "ai_prediction": ai_prediction,
    }


# ==================== 内部辅助函数 ====================
def _get_latest_prediction(db: Session) -> dict:
    """获取最新 AI 预测结果，转为可序列化的 dict。"""
    pred = (
        db.query(AIPrediction)
        .order_by(AIPrediction.predict_time.desc())
        .first()
    )
    if not pred:
        return None
    return {
        "activity": pred.activity_index,
        "scene": pred.scene,
        "scene_probability": pred.scene_probability,
        "light_will_change": pred.light_will_change,
        "light_change_probability": pred.light_change_probability,
        "night_anomaly": {
            "is_anomalous": pred.is_night_anomalous,
            "zscore": pred.night_zscore,
            "current_motion_5min": pred.night_current_motion,
            "threshold": None,  # 阈值记录在 baseline.json 中
        },
    }


def _build_full_context(db: Session) -> str:
    """从 DB 构造完整三层上下文字符串。"""
    latest = (
        db.query(EnvMonitorData)
        .order_by(EnvMonitorData.timestamp.desc())
        .first()
    )
    env_data = None
    if latest:
        env_data = {
            "temperature": latest.sht30_temp_raw,
            "humidity": latest.sht30_humi_raw,
            "light": latest.bh1750_raw,
            "body_state": "有人" if latest.pir_gpio == 1 else "无人",
            "timestamp": str(latest.timestamp),
            "lightStatus": (latest.lightStatus or "").upper() == "ON",
            "motorStatus": (latest.motorStatus or "").upper() == "ON",
        }
    return build_agent_context(env_data, _get_latest_prediction(db))
