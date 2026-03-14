from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.db import models


async def log_request(
    db: AsyncSession,
    org_id: str | None,
    project_id: str,
    api_key_id: str | None,
    owner_user_id: str | None,
    provider: str,
    model: str,
    endpoint: str,
    status: int,
    latency_ms: int,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    cost_usd: float,
    error_code: str | None = None,
    error_message: str | None = None,
) -> None:
    record = models.RequestLog(
        org_id=org_id,
        project_id=project_id,
        api_key_id=api_key_id,
        owner_user_id=owner_user_id,
        provider=provider,
        model=model,
        endpoint=endpoint,
        status=status,
        latency_ms=latency_ms,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        cost_usd=cost_usd,
        error_code=error_code,
        error_message=error_message,
    )
    db.add(record)
    await db.commit()
