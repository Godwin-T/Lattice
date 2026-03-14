from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.db import models
from app.db.session import get_db
from app.schemas.pricing import (
    ModelPricingCreateRequest,
    ModelPricingResponse,
    ModelPricingUpdateRequest,
)


router = APIRouter(prefix="/pricing", tags=["pricing"])


@router.get("", response_model=list[ModelPricingResponse])
async def list_pricing(membership=Depends(require_admin), db: AsyncSession = Depends(get_db)):
    del membership
    result = await db.execute(select(models.ModelPricing).order_by(models.ModelPricing.provider, models.ModelPricing.model))
    items = result.scalars().all()
    return [
        ModelPricingResponse(
            id=item.id,
            provider=item.provider,
            model=item.model,
            model_type=item.model_type,
            cost_per_1m_tokens=float(item.cost_per_1m_tokens),
            active=item.active,
            updated_at=item.updated_at.isoformat(),
            created_at=item.created_at.isoformat(),
        )
        for item in items
    ]


@router.post("", response_model=ModelPricingResponse)
async def create_pricing(
    payload: ModelPricingCreateRequest,
    membership=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    del membership
    item = models.ModelPricing(
        provider=payload.provider.lower(),
        model=payload.model,
        model_type=payload.model_type.lower(),
        cost_per_1m_tokens=payload.cost_per_1m_tokens,
        active=payload.active,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return ModelPricingResponse(
        id=item.id,
        provider=item.provider,
        model=item.model,
        model_type=item.model_type,
        cost_per_1m_tokens=float(item.cost_per_1m_tokens),
        active=item.active,
        updated_at=item.updated_at.isoformat(),
        created_at=item.created_at.isoformat(),
    )


@router.patch("/{pricing_id}", response_model=ModelPricingResponse)
async def update_pricing(
    pricing_id: str,
    payload: ModelPricingUpdateRequest,
    membership=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    del membership
    item = await db.get(models.ModelPricing, pricing_id)
    if not item:
        raise HTTPException(status_code=404, detail="Pricing entry not found")
    if payload.provider is not None:
        item.provider = payload.provider.lower()
    if payload.model is not None:
        item.model = payload.model
    if payload.model_type is not None:
        item.model_type = payload.model_type.lower()
    if payload.cost_per_1m_tokens is not None:
        item.cost_per_1m_tokens = payload.cost_per_1m_tokens
    if payload.active is not None:
        item.active = payload.active
    await db.commit()
    await db.refresh(item)
    return ModelPricingResponse(
        id=item.id,
        provider=item.provider,
        model=item.model,
        model_type=item.model_type,
        cost_per_1m_tokens=float(item.cost_per_1m_tokens),
        active=item.active,
        updated_at=item.updated_at.isoformat(),
        created_at=item.created_at.isoformat(),
    )


@router.delete("/{pricing_id}")
async def delete_pricing(
    pricing_id: str,
    membership=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    del membership
    item = await db.get(models.ModelPricing, pricing_id)
    if not item:
        raise HTTPException(status_code=404, detail="Pricing entry not found")
    await db.delete(item)
    await db.commit()
    return {"status": "ok"}
