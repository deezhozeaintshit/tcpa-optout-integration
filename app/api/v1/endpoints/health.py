import logging
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

logger = logging.getLogger("optout_health")

router = APIRouter(tags=["Health"])


@router.get("/health")
async def healthcheck():
    """Liveness probe — returns 200 if the process is responsive."""
    return {"status": "ok", "service": "tcpa-optout-integration-layer"}


@router.get("/ready")
async def readiness(db: AsyncSession = Depends(get_db)):
    """Readiness probe — verifies the process can reach its database."""
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "ok"}
    except Exception as exc:
        logger.exception("Readiness check failed")
        return {"status": "degraded", "database": "unreachable", "error": str(exc)}
