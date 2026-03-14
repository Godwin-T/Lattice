from __future__ import annotations

from fastapi import Cookie, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import get_settings
from app.db.session import get_db
from app.services.user_auth import get_user_by_session


settings = get_settings()


async def get_current_user(
    session_token: str | None = Cookie(default=None, alias=settings.session_cookie_name),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_by_session(db, session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user
