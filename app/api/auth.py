from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Cookie, Depends, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth_deps import get_current_user
from app.core.settings import get_settings
from app.db import models
from app.db.session import get_db
from app.schemas.auth import LoginRequest, UserResponse
from app.services.auth_errors import AuthError
from app.services.user_auth import create_session, revoke_session, verify_password


router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


@router.post("/login", response_model=UserResponse)
async def login(payload: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    email = payload.email.lower()
    result = await db.execute(select(models.User).where(models.User.email == email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise AuthError("INVALID_CREDENTIALS", "Invalid email or password", status_code=401)
    if user.status != "active":
        raise AuthError("USER_INACTIVE", "User is inactive", status_code=403)

    user.last_login_at = dt.datetime.now(dt.timezone.utc)
    await db.commit()

    token = await create_session(db, user)
    _set_session_cookie(response, token)
    return UserResponse(id=user.id, email=user.email, status=user.status)


@router.post("/logout")
async def logout(
    response: Response,
    session_token: str | None = Cookie(default=None, alias=settings.session_cookie_name),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    del current_user
    await revoke_session(db, session_token)
    response.delete_cookie(settings.session_cookie_name, path="/")
    return {"status": "ok"}


@router.get("/me", response_model=UserResponse)
async def me(current_user=Depends(get_current_user)):
    return UserResponse(id=current_user.id, email=current_user.email, status=current_user.status)


def _set_session_cookie(response: Response, token: str) -> None:
    max_age = settings.session_ttl_hours * 3600
    response.set_cookie(
        settings.session_cookie_name,
        token,
        max_age=max_age,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        path="/",
    )
