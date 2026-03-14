from __future__ import annotations

import datetime as dt
import hmac
import hashlib
import secrets

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import get_settings
from app.db import models


settings = get_settings()
_pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _pwd_context.verify(password, password_hash)


def _hash_session_token(token: str) -> str:
    secret = settings.session_secret.encode("utf-8")
    return hmac.new(secret, token.encode("utf-8"), hashlib.sha256).hexdigest()


def _session_expiry() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=settings.session_ttl_hours)


async def create_session(db: AsyncSession, user: models.User) -> str:
    raw_token = secrets.token_urlsafe(32)
    token_hash = _hash_session_token(raw_token)
    expires_at = _session_expiry()

    session = models.Session(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(session)
    await db.commit()
    return raw_token


async def get_user_by_session(db: AsyncSession, raw_token: str | None) -> models.User | None:
    if not raw_token:
        return None
    token_hash = _hash_session_token(raw_token)
    result = await db.execute(
        select(models.Session, models.User)
        .join(models.User, models.Session.user_id == models.User.id)
        .where(models.Session.token_hash == token_hash)
    )
    row = result.first()
    if not row:
        return None
    session, user = row
    now = dt.datetime.now(dt.timezone.utc)
    if session.expires_at < now or user.status != "active":
        return None
    return user


async def revoke_session(db: AsyncSession, raw_token: str | None) -> None:
    if not raw_token:
        return
    token_hash = _hash_session_token(raw_token)
    result = await db.execute(select(models.Session).where(models.Session.token_hash == token_hash))
    session = result.scalar_one_or_none()
    if not session:
        return
    await db.delete(session)
    await db.commit()
