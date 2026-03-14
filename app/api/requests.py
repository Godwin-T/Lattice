from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_membership
from app.db import models
from app.db.session import get_db
from app.schemas.requests import RequestLogItem, RequestLogResponse


router = APIRouter(prefix="/requests", tags=["requests"])


@router.get("", response_model=RequestLogResponse)
async def list_requests(
    membership=Depends(get_current_membership),
    db: AsyncSession = Depends(get_db),
    org_id: str | None = Query(default=None),
    project_id: str | None = Query(default=None),
    user_id: str | None = Query(default=None),
    key_id: str | None = Query(default=None),
):
    if org_id and org_id != membership.org_id:
        raise HTTPException(status_code=403, detail="Invalid org")

    stmt = select(models.RequestLog).where(models.RequestLog.org_id == membership.org_id)
    if project_id:
        stmt = stmt.where(models.RequestLog.project_id == project_id)
    if user_id:
        stmt = stmt.where(models.RequestLog.owner_user_id == user_id)
    if key_id:
        stmt = stmt.where(models.RequestLog.api_key_id == key_id)

    stmt = stmt.order_by(models.RequestLog.created_at.desc()).limit(200)
    result = await db.execute(stmt)

    items = [
        RequestLogItem(
            id=row.id,
            created_at=row.created_at.isoformat(),
            org_id=row.org_id,
            project_id=row.project_id,
            api_key_id=row.api_key_id,
            owner_user_id=row.owner_user_id,
            provider=row.provider,
            model=row.model,
            status=row.status,
            latency_ms=row.latency_ms,
            cost_usd=float(row.cost_usd),
        )
        for row in result.scalars().all()
    ]

    return RequestLogResponse(items=items)
