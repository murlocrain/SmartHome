import sys as _sys
import os as _os
# 添加 ai/src/ 到 sys.path
_AI_SRC = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..', '..', 'ai', 'src'))
if _AI_SRC not in _sys.path:
    _sys.path.insert(0, _AI_SRC)

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from common.config import settings, logger
from common.database import init_database
from common.iot_client import iot_client
from common.websocket_manager import manager as ws_manager

from APP.api.devices import router as devices_router
from APP.api.data import router as data_router
from APP.api.control import router as control_router
from APP.api.callback import router as callback_router
from APP.api.ai import router as ai_router

from ai_service import predictor


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()
    if settings.HUAWEI_IOTDA_ENABLED:
        _ = iot_client.client
        logger.info("REST API主动拉取已禁用，仅使用数据转发回调")
    try:
        predictor.load_models()
    except Exception as e:
        logger.error(f"AI模型加载失败: {e}")
    yield


app = FastAPI(
    title="智能家居后端",
    description="智能家居后端系统（模块化版本）",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"[请求] {request.method} {request.url.path} 来源={request.client.host if request.client else 'unknown'}")
    try:
        body_bytes = await request.body()
        if body_bytes:
            body_text = body_bytes.decode("utf-8")
            preview = body_text[:300]
            logger.info(f"[请求体] {preview}")
    except Exception:
        pass
    return await call_next(request)


app.include_router(devices_router)
app.include_router(data_router)
app.include_router(control_router)
app.include_router(callback_router)
app.include_router(ai_router)


@app.get("/")
def read_root():
    return {
        "message": "智能家居后端服务运行中（模块化架构）",
        "database": settings.DATABASE_TYPE,
        "huawei_iot": settings.HUAWEI_IOTDA_ENABLED,
        "version": "2.0.0",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.websocket("/ws/{family_id}")
async def websocket_endpoint(ws: WebSocket, family_id: str):
    """WebSocket 端点：前端连接后接收实时传感器推送。
    前端连接格式: ws://localhost:8000/ws/{family_id}
    """
    await ws_manager.connect(ws)
    try:
        while True:
            raw = await ws.receive_text()
            # 只处理心跳 ping → pong，其余消息忽略
            import json as _json
            try:
                msg = _json.loads(raw)
                if msg.get("type") == "ping":
                    await ws.send_json({"type": "pong"})
            except Exception:
                pass
    except WebSocketDisconnect:
        await ws_manager.disconnect(ws)
    except Exception:
        await ws_manager.disconnect(ws)


if __name__ == "__main__":
    import uvicorn

    logger.info(f"启动服务: http://0.0.0.0:8000")
    logger.info(f"回调接口: http://0.0.0.0:8000/api/v1/devices/huawei-callback")
    logger.info(f"API文档: http://localhost:8000/docs")

    uvicorn.run("APP.main:app", host="0.0.0.0", port=8000, reload=False)
