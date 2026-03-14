from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_membership, require_admin
from app.db import models
from app.db.session import get_db
from app.schemas.auth import APIKeyCreateRequest, APIKeyCreateResponse, APIKeyResponse
from app.services.auth import hash_api_key


router = APIRouter(prefix="/keys", tags=["keys"])


def _key_prefix(raw_key: str) -> str:
    return raw_key[:8]


@router.get("", response_model=list[APIKeyResponse])
async def list_keys(membership=Depends(get_current_membership), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.APIKey)
        .join(models.Project, models.APIKey.project_id == models.Project.id)
        .where(models.Project.org_id == membership.org_id)
        .order_by(models.APIKey.created_at.desc())
    )
    keys = result.scalars().all()
    return [
        APIKeyResponse(
            id=key.id,
            key_prefix=key.key_prefix,
            tag=key.tag,
            status=key.status,
            project_id=key.project_id,
            owner_user_id=key.owner_user_id,
            created_by_user_id=key.created_by_user_id,
            created_at=key.created_at.isoformat(),
            last_used_at=key.last_used_at.isoformat() if key.last_used_at else None,
        )
        for key in keys
    ]


@router.post("", response_model=APIKeyCreateResponse)
async def create_key(
    payload: APIKeyCreateRequest,
    membership=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(models.Project).where(models.Project.id == payload.project_id, models.Project.org_id == membership.org_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    while True:
        raw_key = f"lattice_{secrets.token_urlsafe(32)}"
        key_hash = hash_api_key(raw_key)
        result = await db.execute(select(models.APIKey).where(models.APIKey.key_hash == key_hash))
        existing = result.scalar_one_or_none()
        if existing:
            continue
        api_key = models.APIKey(
            project_id=project.id,
            owner_user_id=membership.user_id,
            created_by_user_id=membership.user_id,
            key_hash=key_hash,
            key_prefix=_key_prefix(raw_key),
            tag=payload.tag,
        )
        db.add(api_key)
        await db.commit()
        await db.refresh(api_key)
        return APIKeyCreateResponse(
            id=api_key.id,
            key=raw_key,
            key_prefix=api_key.key_prefix,
            tag=api_key.tag,
            status=api_key.status,
            project_id=api_key.project_id,
            owner_user_id=api_key.owner_user_id,
            created_by_user_id=api_key.created_by_user_id,
            created_at=api_key.created_at.isoformat(),
        )


@router.post("/{key_id}/revoke")
async def revoke_key(key_id: str, membership=Depends(require_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.APIKey)
        .join(models.Project, models.APIKey.project_id == models.Project.id)
        .where(models.APIKey.id == key_id, models.Project.org_id == membership.org_id)
    )
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    api_key.status = "revoked"
    await db.commit()
    return {"status": "ok"}


@router.delete("/{key_id}")
async def delete_key(key_id: str, membership=Depends(require_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.APIKey)
        .join(models.Project, models.APIKey.project_id == models.Project.id)
        .where(models.APIKey.id == key_id, models.Project.org_id == membership.org_id)
    )
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    await db.delete(api_key)
    await db.commit()
    return {"status": "ok"}
