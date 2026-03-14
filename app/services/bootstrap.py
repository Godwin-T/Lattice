from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import get_settings
from app.db import models
from app.db.session import SessionLocal
from app.services.projects import ensure_default_project
from app.services.user_auth import hash_password


settings = get_settings()


async def ensure_admin_user() -> None:
    async with SessionLocal() as db:
        await _ensure_admin_user(db)


async def _ensure_admin_user(db: AsyncSession) -> None:
    email = settings.admin_email.lower()
    result = await db.execute(select(models.User).where(models.User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        user = models.User(
            email=email,
            password_hash=hash_password(settings.admin_password),
            status="active",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    if user.status != "active":
        user.status = "active"
        await db.commit()

    membership_result = await db.execute(
        select(models.OrgMembership).where(models.OrgMembership.user_id == user.id)
    )
    membership = membership_result.scalar_one_or_none()

    if membership:
        if membership.role != "admin":
            membership.role = "admin"
            await db.commit()
        await ensure_default_project(db, membership.org_id)
        return

    org_result = await db.execute(select(models.Org).where(models.Org.name == settings.admin_org_name))
    org = org_result.scalar_one_or_none()
    if not org:
        org = models.Org(name=settings.admin_org_name)
        db.add(org)
        await db.commit()
        await db.refresh(org)

    membership = models.OrgMembership(org_id=org.id, user_id=user.id, role="admin")
    db.add(membership)
    await db.commit()

    await ensure_default_project(db, org.id)
