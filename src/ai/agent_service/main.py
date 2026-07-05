"""智能体服务 - 端口 8013"""
import sys
import os
# 添加 python/ 目录到 sys.path，以便导入 common.* 模块
_python_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'python'))
if _python_dir not in sys.path:
    sys.path.insert(0, _python_dir)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from common.config import settings
from common.database import init_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()
    yield


app = FastAPI(
    title=f"{settings.PROJECT_NAME} - Agent Service",
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

from .agent_router import router as agent_router
app.include_router(agent_router, prefix=f"{settings.API_V1_PREFIX}/agent")


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "agent-service"}


@app.get("/ready")
async def ready():
    return {"status": "ready"}
