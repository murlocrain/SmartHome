"""智能体服务 - 端口 8013"""
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
