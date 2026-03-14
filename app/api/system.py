from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_redis
from app.db.session import get_db
from app.observability.metrics import metrics_response


router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/ready")
async def readiness(db: AsyncSession = Depends(get_db), redis_client=Depends(get_redis)) -> dict:
    await db.execute(text("SELECT 1"))
    await redis_client.ping()
    return {"status": "ready"}


@router.get("/metrics")
def metrics():
    return metrics_response()
