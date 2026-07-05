"""网关服务 - 路由定义"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from common.config import logger
from common.security import decode_token
from .schemas import ConnectionStatus

router = APIRouter()


@router.websocket("/ws/{family_id}")
async def websocket_endpoint(websocket: WebSocket, family_id: str, token: str = Query(None)):
    """WebSocket 端点：前端连接后接收实时传感器推送。需携带 token 认证。"""
    if not token:
        await websocket.close(code=4001, reason="缺少认证令牌")
        return
    payload = decode_token(token)
    if not payload:
        await websocket.close(code=4001, reason="无效的令牌或令牌已过期")
        return

    from common.websocket_manager import manager as ws_manager

    await ws_manager.connect(websocket)
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                import json as _json
                msg = _json.loads(raw)
                if msg.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except Exception:
                pass
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    except Exception:
        await ws_manager.disconnect(websocket)


@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "gateway-service"}


@router.get("/ready")
async def readiness_check():
    return {"status": "ready"}


@router.get("/connections", response_model=ConnectionStatus)
async def get_connections():
    from common.websocket_manager import manager as ws_manager

    total = ws_manager.connection_count
    families = 1 if total > 0 else 0
    return ConnectionStatus(active_families=families, total_connections=total)


@router.post("/broadcast")
async def broadcast_to_family(data: dict):
    """接收其他服务的广播请求，转发给前端WebSocket连接"""
    from common.websocket_manager import manager as ws_manager
    from datetime import datetime, timezone

    family_id = str(data.get("family_id", "1"))
    message = {
        "type": data.get("type", "device_update"),
        "device_id": data.get("device_id"),
        "data": data.get("data", {}),
        "timestamp": data.get("timestamp", datetime.now(timezone.utc).isoformat()),
    }

    await ws_manager.broadcast(message)
    logger.info(f"Broadcast sent to family {family_id}, {ws_manager.connection_count} active connections")

    return {"status": "success", "family_id": family_id, "connections": ws_manager.connection_count}
