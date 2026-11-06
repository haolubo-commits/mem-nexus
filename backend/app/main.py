"""
Main FastAPI application entrypoint for MemNexus.
"""

from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.mongodb import db_manager
from app.routers import health_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("mem_nexus")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to DB and ensure indexes
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}...")
    await db_manager.connect()
    yield
    # Shutdown: Clean up connections
    logger.info(f"Shutting down {settings.PROJECT_NAME}...")
    await db_manager.close()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    lifespan=lifespan,
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Root"])
async def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": f"{settings.API_V1_PREFIX}/docs",
        "health_url": f"{settings.API_V1_PREFIX}/health",
        "description": settings.DESCRIPTION,
    }
