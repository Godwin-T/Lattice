from __future__ import annotations

import datetime as dt
import hmac
import hashlib

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.settings import get_settings
from app.db import models

settings = get_settings()


def hash_api_key(raw_key: str) -> str:
    secret = settings.api_key_secret.encode("utf-8")
    return hmac.new(secret, raw_key.encode("utf-8"), hashlib.sha256).hexdigest()


async def validate_api_key(db: AsyncSession, raw_key: str) -> models.APIKey | None:
    key_hash = hash_api_key(raw_key)
    result = await db.execute(
        select(models.APIKey)
        .options(selectinload(models.APIKey.project))
        .where(models.APIKey.key_hash == key_hash, models.APIKey.status == "active")
    )
    api_key = result.scalar_one_or_none()
    if not api_key:
        return None
    if api_key.owner_user_id:
        user_result = await db.execute(select(models.User).where(models.User.id == api_key.owner_user_id))
        user = user_result.scalar_one_or_none()
        if not user or user.status != "active":
            return None
    api_key.last_used_at = dt.datetime.now(dt.timezone.utc)
    await db.commit()
    return api_key
