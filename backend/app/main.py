from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routes import memories
from app.services.redis_service import redis_service
from app.services.qdrant_service import qdrant_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure Qdrant collection exists
    try:
        await qdrant_service.ensure_collection()
    except Exception:
        pass

    yield

    # Shutdown: close connections
    try:
        await redis_service.close()
    except Exception:
        pass
    try:
        qdrant_service.close()
    except Exception:
        pass


app = FastAPI(
    title="MyPersonalPensieve API",
    version="2.0.0",
    description="AI Personal Memory System - Python Backend",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(memories.router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}
