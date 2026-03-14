from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_membership
from app.db import models
from app.db.session import get_db
from app.schemas.usage import (
    UsageByKeyItem,
    UsageByKeyResponse,
    UsageByProjectItem,
    UsageByProjectResponse,
    UsageByUserItem,
    UsageByUserResponse,
    UsageOverviewResponse,
)


router = APIRouter(prefix="/usage", tags=["usage"])


def _validate_org_id(membership, org_id: str | None) -> str:
    if org_id and org_id != membership.org_id:
        raise HTTPException(status_code=403, detail="Invalid org")
    return membership.org_id


@router.get("/overview", response_model=UsageOverviewResponse)
async def overview(
    membership=Depends(get_current_membership),
    db: AsyncSession = Depends(get_db),
    org_id: str | None = Query(default=None),
    project_id: str | None = Query(default=None),
):
    org_id = _validate_org_id(membership, org_id)

    stmt = select(
        func.count(models.RequestLog.id),
        func.coalesce(func.sum(models.RequestLog.cost_usd), 0.0),
        func.coalesce(func.sum(models.RequestLog.total_tokens), 0),
        func.coalesce(func.avg(models.RequestLog.latency_ms), 0.0),
    ).where(models.RequestLog.org_id == org_id)

    if project_id:
        stmt = stmt.where(models.RequestLog.project_id == project_id)

    result = await db.execute(stmt)
    total_requests, total_cost, total_tokens, avg_latency = result.one()

    return UsageOverviewResponse(
        total_requests=int(total_requests or 0),
        total_cost_usd=float(total_cost or 0.0),
        total_tokens=int(total_tokens or 0),
        avg_latency_ms=float(avg_latency or 0.0),
    )


@router.get("/by-user", response_model=UsageByUserResponse)
async def by_user(
    membership=Depends(get_current_membership),
    db: AsyncSession = Depends(get_db),
    org_id: str | None = Query(default=None),
):
    org_id = _validate_org_id(membership, org_id)

    result = await db.execute(
        select(
            models.RequestLog.owner_user_id,
            func.count(models.RequestLog.id),
            func.coalesce(func.sum(models.RequestLog.cost_usd), 0.0),
            func.coalesce(func.sum(models.RequestLog.total_tokens), 0),
            func.coalesce(func.avg(models.RequestLog.latency_ms), 0.0),
        )
        .where(models.RequestLog.org_id == org_id)
        .group_by(models.RequestLog.owner_user_id)
        .order_by(models.RequestLog.owner_user_id)
    )

    items = []
    for owner_user_id, requests, cost, tokens, avg_latency in result.all():
        email = None
        if owner_user_id:
            user_result = await db.execute(select(models.User.email).where(models.User.id == owner_user_id))
            email = user_result.scalar_one_or_none()
        items.append(
            UsageByUserItem(
                user_id=owner_user_id,
                email=email,
                requests=int(requests or 0),
                cost_usd=float(cost or 0.0),
                tokens=int(tokens or 0),
                avg_latency_ms=float(avg_latency or 0.0),
            )
        )

    return UsageByUserResponse(items=items)


@router.get("/by-project", response_model=UsageByProjectResponse)
async def by_project(
    membership=Depends(get_current_membership),
    db: AsyncSession = Depends(get_db),
    org_id: str | None = Query(default=None),
):
    org_id = _validate_org_id(membership, org_id)

    result = await db.execute(
        select(
            models.Project.id,
            models.Project.name,
            func.count(models.RequestLog.id),
            func.coalesce(func.sum(models.RequestLog.cost_usd), 0.0),
            func.coalesce(func.sum(models.RequestLog.total_tokens), 0),
            func.coalesce(func.avg(models.RequestLog.latency_ms), 0.0),
        )
        .join(models.RequestLog, models.RequestLog.project_id == models.Project.id)
        .where(models.Project.org_id == org_id)
        .group_by(models.Project.id, models.Project.name)
        .order_by(models.Project.name)
    )

    items = [
        UsageByProjectItem(
            project_id=row[0],
            project_name=row[1],
            requests=int(row[2] or 0),
            cost_usd=float(row[3] or 0.0),
            tokens=int(row[4] or 0),
            avg_latency_ms=float(row[5] or 0.0),
        )
        for row in result.all()
    ]

    return UsageByProjectResponse(items=items)


@router.get("/by-key", response_model=UsageByKeyResponse)
async def by_key(
    membership=Depends(get_current_membership),
    db: AsyncSession = Depends(get_db),
    project_id: str = Query(...),
):
    result = await db.execute(select(models.Project).where(models.Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project or project.org_id != membership.org_id:
        raise HTTPException(status_code=404, detail="Project not found")

    result = await db.execute(
        select(
            models.APIKey.id,
            models.APIKey.key_prefix,
            models.APIKey.owner_user_id,
            func.count(models.RequestLog.id),
            func.coalesce(func.sum(models.RequestLog.cost_usd), 0.0),
            func.coalesce(func.sum(models.RequestLog.total_tokens), 0),
            func.coalesce(func.avg(models.RequestLog.latency_ms), 0.0),
        )
        .join(models.RequestLog, models.RequestLog.api_key_id == models.APIKey.id)
        .where(models.APIKey.project_id == project_id)
        .group_by(models.APIKey.id, models.APIKey.key_prefix, models.APIKey.owner_user_id)
        .order_by(models.APIKey.created_at.desc())
    )

    items = [
        UsageByKeyItem(
            api_key_id=row[0],
            key_prefix=row[1],
            owner_user_id=row[2],
            requests=int(row[3] or 0),
            cost_usd=float(row[4] or 0.0),
            tokens=int(row[5] or 0),
            avg_latency_ms=float(row[6] or 0.0),
        )
        for row in result.all()
    ]

    return UsageByKeyResponse(items=items)
