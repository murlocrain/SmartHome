"""
智能体服务路由
提供自然语言 → 设备控制的完整链路：
  1. POST /agent/chat    — 普通聊天
  2. POST /agent/control — 智能控制（解析意图 + 执行）
  3. WebSocket /agent/ws — 流式对话
"""
import sys
import os
# 添加 python/ 目录到 sys.path，以便导入 common.* 模块
_python_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'python'))
if _python_dir not in sys.path:
    sys.path.insert(0, _python_dir)

import json as _json
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session
from common.config import settings, logger
from common.database import get_db
from common.security import get_current_user_id, decode_token
from .ai_client import chat_with_ai, parse_intent, analyze_environment, iot_client, _build_full_context
from .schemas import ChatRequest, ChatResponse, AgentControlRequest, AgentControlResponse

router = APIRouter()


# ──────────────────── REST: 简单聊天 ────────────────────
@router.post("/chat", response_model=ChatResponse)
def agent_chat(
    request: ChatRequest,
    user_id: int = Depends(get_current_user_id),
):
    """聊天接口，自动注入环境+AI预测上下文。"""
    full_ctx = _build_full_context()
    reply = chat_with_ai(request.message, extra_context=full_ctx)
    return ChatResponse(message=request.message, reply=reply, model=settings.AI_MODEL)


# ──────────────────── REST: 智能控制 ────────────────────
@router.post("/control", response_model=AgentControlResponse)
def agent_control(
    request: AgentControlRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    parsed = parse_intent(request.message)
    intent = parsed.get("intent", "chat")
    target = parsed.get("target")
    action = parsed.get("action")
    reply = parsed.get("reply", "")

    device_result = None

    # 意图 → 执行控制
    if intent == "control" and target and action:
        cmd_map = {
            "light": ("light_control", {"onoff": action}),
            "motor": ("motor_control", {"onoff": action}),
            "beep": ("beep_play", {}),
        }
        cmd = cmd_map.get(target)
        if cmd and settings.HUAWEI_IOTDA_ENABLED:
            try:
                r = iot_client.send_command(cmd[0], cmd[1])
                device_result = r
                logger.info(f"[Agent] {target} → {action}  result={'ok' if r.get('success') else 'fail'}")
            except Exception as e:
                logger.error(f"[Agent] 控制执行异常: {e}")
                device_result = {"error": str(e)}
                reply = f"抱歉，{target}控制执行失败：{e}"

    # 统一用完整上下文（传感器+AI预测）生成智能回复
    full_ctx = _build_full_context()
    ai_reply = chat_with_ai(request.message, extra_context=full_ctx) if full_ctx else reply

    return AgentControlResponse(
        message=request.message,
        reply=ai_reply,
        intent=intent,
        target=target,
        action=action,
        device_result=device_result,
        current_env=full_ctx,
        suggestion=ai_reply,
    )


# ──────────────────── WebSocket: 流式对话 ────────────────────
@router.websocket("/ws/{family_id}")
async def agent_websocket(
    websocket: WebSocket,
    family_id: str,
    token: str = Query(None),
):
    if not token:
        await websocket.close(code=4001, reason="缺少认证令牌")
        return
    payload = decode_token(token)
    if not payload:
        await websocket.close(code=4001, reason="无效的令牌或令牌已过期")
        return

    await websocket.accept()
    logger.info(f"[Agent-WS] family={family_id} 已连接")

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = _json.loads(raw)
            except _json.JSONDecodeError:
                await websocket.send_json({"type": "error", "content": "消息格式错误"})
                continue

            if msg.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            user_message = msg.get("message", "").strip()
            mode = msg.get("mode", "chat")  # chat | agent

            if not user_message:
                await websocket.send_json({"type": "error", "content": "消息不能为空"})
                continue

            # Agent 模式：先解析意图
            if mode == "agent":
                parsed = parse_intent(user_message)
                intent = parsed.get("intent", "chat")
                target = parsed.get("target")
                action = parsed.get("action")
                reply = parsed.get("reply", "")

                device_result = None
                if intent == "control" and target and action:
                    cmd_map = {
                        "light": ("light_control", {"onoff": action}),
                        "motor": ("motor_control", {"onoff": action}),
                        "beep": ("beep_play", {}),
                    }
                    cmd = cmd_map.get(target)
                    if cmd and settings.HUAWEI_IOTDA_ENABLED:
                        try:
                            r = iot_client.send_command(cmd[0], cmd[1])
                            device_result = r
                        except Exception as e:
                            device_result = {"error": str(e)}
                            reply = f"抱歉，控制失败：{e}"

                await websocket.send_json({
                    "type": "agent_result",
                    "message": user_message,
                    "reply": reply,
                    "intent": intent,
                    "target": target,
                    "action": action,
                    "device_result": device_result,
                })

                # 如果是 question，追加环境分析
                if intent == "question":
                    full_ctx = _build_full_context()
                    suggestion = chat_with_ai(user_message, extra_context=full_ctx)
                    await websocket.send_json({
                        "type": "suggestion",
                        "content": suggestion,
                        "env": full_ctx,
                    })

            else:
                # Chat 模式：用完整上下文回答
                full_ctx = _build_full_context()
                reply = chat_with_ai(user_message, extra_context=full_ctx)
                await websocket.send_json({
                    "type": "chat_reply",
                    "message": user_message,
                    "reply": reply,
                })

    except WebSocketDisconnect:
        logger.info(f"[Agent-WS] family={family_id} 断开")
    except Exception as e:
        logger.error(f"[Agent-WS] 异常: {e}")
