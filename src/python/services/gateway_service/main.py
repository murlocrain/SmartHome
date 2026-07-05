"""
网关服务 - 主入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from common.config import settings
from .gateway_router import router as gateway_router

app = FastAPI(
    title=f"{settings.PROJECT_NAME} - Gateway Service",
    version=settings.VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(gateway_router)


@app.on_event("startup")
async def startup_event():
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Gateway service started")


@app.on_event("shutdown")
async def shutdown_event():
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Gateway service stopped")
