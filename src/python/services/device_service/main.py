import sys as _sys
import os as _os
_AI_SRC = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..', '..', 'ai', 'src'))
if _AI_SRC not in _sys.path:
    _sys.path.insert(0, _AI_SRC)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from common.config import settings, logger
from common.database import init_database
from common.iot_client import iot_client
from .device_router import router as device_router, callback_router as callback_router, analysis_router as analysis_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()
    # 加载 AI 预测模型
    try:
        from ai_service import predictor
        predictor.load_models()
        logger.info("AI 预测模型加载完成")
    except Exception as e:
        logger.error(f"AI 预测模型加载失败: {e}")
    if settings.HUAWEI_IOTDA_ENABLED:
        _ = iot_client.client
        logger.info("REST API主动拉取已禁用，仅使用数据转发回调")
    yield


app = FastAPI(
    title=f"{settings.PROJECT_NAME} - Device Service",
    version=settings.VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(device_router, prefix=settings.API_V1_PREFIX)
app.include_router(callback_router)
app.include_router(analysis_router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "device-service"}


@app.get("/ready")
async def readiness_check():
    return {"status": "ready"}
