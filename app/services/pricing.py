from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import pricing as static_pricing
from app.db import models


async def get_cost_per_1m_tokens(
    db: AsyncSession,
    provider: str,
    model: str,
    model_type: str,
) -> float | None:
    result = await db.execute(
        select(models.ModelPricing).where(
            models.ModelPricing.provider == provider,
            models.ModelPricing.model == model,
            models.ModelPricing.model_type == model_type,
            models.ModelPricing.active.is_(True),
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        return None
    return float(item.cost_per_1m_tokens)


async def pick_model_for_provider(
    db: AsyncSession,
    provider: str,
    model_type: str,
    requested_model: str,
) -> str | None:
    # Use requested model if pricing entry exists for this provider/type.
    result = await db.execute(
        select(models.ModelPricing.model).where(
            models.ModelPricing.provider == provider,
            models.ModelPricing.model_type == model_type,
            models.ModelPricing.model == requested_model,
            models.ModelPricing.active.is_(True),
        )
    )
    if result.scalar_one_or_none():
        return requested_model

    # Otherwise pick first active model for provider/type.
    result = await db.execute(
        select(models.ModelPricing.model)
        .where(
            models.ModelPricing.provider == provider,
            models.ModelPricing.model_type == model_type,
            models.ModelPricing.active.is_(True),
        )
        .order_by(models.ModelPricing.model)
        .limit(1)
    )
    return result.scalar_one_or_none()


async def compute_chat_cost(
    db: AsyncSession,
    provider: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> float:
    cost_per_1m = await get_cost_per_1m_tokens(db, provider, model, "chat")
    if cost_per_1m is not None:
        total_tokens = prompt_tokens + completion_tokens
        return (total_tokens / 1_000_000.0) * cost_per_1m
    return static_pricing.compute_chat_cost(provider, model, prompt_tokens, completion_tokens)


async def compute_embedding_cost(
    db: AsyncSession,
    provider: str,
    model: str,
    total_tokens: int,
) -> float:
    cost_per_1m = await get_cost_per_1m_tokens(db, provider, model, "embedding")
    if cost_per_1m is not None:
        return (total_tokens / 1_000_000.0) * cost_per_1m
    return static_pricing.compute_embedding_cost(provider, model, total_tokens)
