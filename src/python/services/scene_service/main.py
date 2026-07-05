from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from common.config import settings

app = FastAPI(
    title=f"{settings.PROJECT_NAME} - Scene Service",
    version=settings.VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from .scene_router import router as scene_router
app.include_router(scene_router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "scene-service"}


@app.get("/ready")
async def readiness_check():
    return {"status": "ready"}
