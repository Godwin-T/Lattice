from __future__ import annotations

import redis.asyncio as redis
from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession


from app.api.auth_deps import get_current_user
from app.services.orgs import get_membership
from app.core.settings import get_settings
from app.db.session import get_db
from app.schemas.errors import OpenAIError
from app.services.auth import validate_api_key
from app.services.rate_limit import RateLimiter
from app.services.providers.router import ProviderRouter, get_provider_router


settings = get_settings()


def get_redis() -> redis.Redis:
    return redis.Redis.from_url(settings.redis_url, decode_responses=True)


def get_rate_limiter(redis_client: redis.Redis = Depends(get_redis)) -> RateLimiter:
    return RateLimiter(redis_client, settings.rate_limit_rpm)


async def get_current_api_key(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    
    if not authorization or not authorization.startswith("Bearer "):
        raise OpenAIError("Missing or invalid Authorization header", status_code=401, error_type="authentication_error")
    raw_key = authorization.replace("Bearer ", "", 1).strip()
    api_key = await validate_api_key(db, raw_key)
    if not api_key:
        raise OpenAIError("Invalid API key", status_code=401, error_type="authentication_error")
    return api_key


def get_provider_router_dep() -> ProviderRouter:
    return get_provider_router()


async def get_current_membership(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    membership = await get_membership(db, current_user.id)
    if not membership:
        raise HTTPException(status_code=403, detail="No organization membership")
    return membership


async def require_admin(membership=Depends(get_current_membership)):
    if membership.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    return membership