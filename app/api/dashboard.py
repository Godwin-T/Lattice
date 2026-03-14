from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_membership
from app.core.settings import get_settings
from app.db import models
from app.db.session import get_db
from app.schemas.dashboard import (
    OverviewResponse,
    ProviderBreakdown,
    ProviderItem,
    ProvidersResponse,
    RequestItem,
    RequestsResponse,
    TrendPoint,
    UsagePoint,
    UsageResponse,
)


router = APIRouter(prefix="/dashboard", tags=["dashboard"])
settings = get_settings()


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


@router.get("/overview", response_model=OverviewResponse)
async def overview(membership=Depends(get_current_membership), db: AsyncSession = Depends(get_db)):
    total_result = await db.execute(
        select(func.count(models.RequestLog.id)).where(models.RequestLog.org_id == membership.org_id)
    )
    total_requests = total_result.scalar_one() or 0

    success_result = await db.execute(
        select(func.count(models.RequestLog.id)).where(
            models.RequestLog.org_id == membership.org_id,
            models.RequestLog.status >= 200,
            models.RequestLog.status < 300,
        )
    )
    success_count = success_result.scalar_one() or 0
    success_rate = (success_count / total_requests * 100.0) if total_requests else 0.0

    cost_result = await db.execute(
        select(func.coalesce(func.sum(models.RequestLog.cost_usd), 0.0)).where(
            models.RequestLog.org_id == membership.org_id
        )
    )
    total_cost = float(cost_result.scalar_one() or 0.0)

    latency_result = await db.execute(
        select(func.coalesce(func.avg(models.RequestLog.latency_ms), 0.0)).where(
            models.RequestLog.org_id == membership.org_id
        )
    )
    avg_latency = float(latency_result.scalar_one() or 0.0)

    start = _utcnow() - dt.timedelta(days=7)
    trend_result = await db.execute(
        select(func.date(models.RequestLog.created_at).label("day"), func.count(models.RequestLog.id))
        .where(models.RequestLog.org_id == membership.org_id, models.RequestLog.created_at >= start)
        .group_by("day")
        .order_by("day")
    )
    trend = [TrendPoint(date=str(row[0]), value=float(row[1])) for row in trend_result.all()]

    return OverviewResponse(
        total_requests=int(total_requests),
        success_rate=round(success_rate, 2),
        total_cost_usd=round(total_cost, 4),
        avg_latency_ms=round(avg_latency, 2),
        trend=trend,
    )


@router.get("/usage", response_model=UsageResponse)
async def usage(membership=Depends(get_current_membership), db: AsyncSession = Depends(get_db)):
    start = _utcnow() - dt.timedelta(days=14)

    by_day_result = await db.execute(
        select(
            func.date(models.RequestLog.created_at).label("day"),
            func.coalesce(func.sum(models.RequestLog.total_tokens), 0),
            func.coalesce(func.sum(models.RequestLog.cost_usd), 0.0),
        )
        .where(models.RequestLog.org_id == membership.org_id, models.RequestLog.created_at >= start)
        .group_by("day")
        .order_by("day")
    )
    by_day = [
        UsagePoint(date=str(row[0]), tokens=int(row[1]), cost_usd=float(row[2]))
        for row in by_day_result.all()
    ]

    provider_result = await db.execute(
        select(
            models.RequestLog.provider,
            func.count(models.RequestLog.id),
            func.coalesce(func.sum(models.RequestLog.cost_usd), 0.0),
        )
        .where(models.RequestLog.org_id == membership.org_id)
        .group_by(models.RequestLog.provider)
        .order_by(models.RequestLog.provider)
    )
    provider_breakdown = [
        ProviderBreakdown(provider=row[0], requests=int(row[1]), cost_usd=float(row[2]))
        for row in provider_result.all()
    ]

    return UsageResponse(by_day=by_day, provider_breakdown=provider_breakdown)


@router.get("/requests", response_model=RequestsResponse)
async def requests(
    membership=Depends(get_current_membership),
    db: AsyncSession = Depends(get_db),
    provider: str | None = Query(default=None),
    status: int | None = Query(default=None),
):
    stmt = (
        select(models.RequestLog)
        .where(models.RequestLog.org_id == membership.org_id)
        .order_by(models.RequestLog.created_at.desc())
        .limit(100)
    )
    if provider:
        stmt = stmt.where(models.RequestLog.provider == provider)
    if status is not None:
        stmt = stmt.where(models.RequestLog.status == status)

    result = await db.execute(stmt)
    items = [
        RequestItem(
            id=row.id,
            created_at=row.created_at.isoformat(),
            provider=row.provider,
            model=row.model,
            status=row.status,
            latency_ms=row.latency_ms,
            cost_usd=float(row.cost_usd),
        )
        for row in result.scalars().all()
    ]

    return RequestsResponse(items=items)


@router.get("/providers", response_model=ProvidersResponse)
async def providers(membership=Depends(get_current_membership)):
    del membership
    items = [
        ProviderItem(provider="openai", enabled=bool(settings.openai_api_key)),
        ProviderItem(provider="anthropic", enabled=bool(settings.anthropic_api_key)),
        ProviderItem(provider="groq", enabled=bool(settings.groq_api_key)),
    ]
    return ProvidersResponse(providers=items, rate_limit_rpm=settings.rate_limit_rpm)
