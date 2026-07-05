from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from common.config import settings
from .auth_router import router as auth_router
from .family_router import router as family_router

app = FastAPI(
    title=f"{settings.PROJECT_NAME} - User Service",
    version=settings.VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(family_router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "user-service"}


@app.get("/ready")
async def readiness_check():
    return {"status": "ready"}
