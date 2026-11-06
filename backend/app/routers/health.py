"""
Health check and system status router.
"""

from datetime import datetime, timezone
from fastapi import APIRouter
from app.config import settings
from app.db.mongodb import db_manager

router = APIRouter(tags=["Health"])


@router.get("/health", summary="System Health & Database Status")
async def health_check():
    db_status = "connected" if (db_manager.db is not None and not db_manager.is_fallback) else "in_memory_fallback"
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": {
            "status": db_status,
            "engine": "mongodb" if not db_manager.is_fallback else "mock_in_memory",
            "name": settings.DATABASE_NAME
        },
        "config": {
            "decay_rate": settings.DEFAULT_DECAY_RATE,
            "max_hops": settings.DEFAULT_MAX_HOPS,
            "min_confidence": settings.MIN_CONFIDENCE_THRESHOLD
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
