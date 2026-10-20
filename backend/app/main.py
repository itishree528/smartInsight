import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.services.cache_service import cache_service
from app.services.local_store import init_local_db
from app.api import documents_router, chat_router, analytics_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("smartinsight")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize pgvector tables and Redis connection
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.PROJECT_VERSION}...")
    try:
        init_local_db()
    except Exception as e:
        logger.warning(f"Local storage init notice: {e}")

    try:
        await init_db()
    except Exception as e:
        logger.warning(f"Database auto-init notice: {e}")

    try:
        await cache_service.connect()
    except Exception as e:
        logger.warning(f"Redis auto-connect notice: {e}")

    yield

    # Shutdown: Close connections
    logger.info("Shutting down SmartInsight services...")
    await cache_service.close()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="AI-Powered Document Search & Analytics Engine using FastAPI, pgvector, Redis, and Next.js.",
    lifespan=lifespan,
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(documents_router, prefix=settings.API_PREFIX)
app.include_router(chat_router, prefix=settings.API_PREFIX)
app.include_router(analytics_router, prefix=settings.API_PREFIX)


@app.get("/", tags=["Health"])
async def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "status": "online",
        "docs_url": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    redis_active = cache_service.redis is not None
    return {
        "status": "healthy",
        "redis_connected": redis_active,
        "embedding_dim": settings.EMBEDDING_DIMENSION,
        "target_ttft_ms": settings.TARGET_TTFT_MS,
    }
