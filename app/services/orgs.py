from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import models


def _org_name_for_email(email: str) -> str:
    return f"{email.split('@')[0]}-org"


async def create_personal_org(db: AsyncSession, user: models.User) -> models.Org:
    org = models.Org(name=_org_name_for_email(user.email))
    db.add(org)
    await db.commit()
    await db.refresh(org)

    membership = models.OrgMembership(org_id=org.id, user_id=user.id, role="admin")
    db.add(membership)

    project = models.Project(org_id=org.id, name="default")
    db.add(project)

    await db.commit()
    return org


async def get_membership(db: AsyncSession, user_id: str) -> models.OrgMembership | None:
    result = await db.execute(select(models.OrgMembership).where(models.OrgMembership.user_id == user_id))
    return result.scalar_one_or_none()


async def get_org(db: AsyncSession, org_id: str) -> models.Org | None:
    result = await db.execute(select(models.Org).where(models.Org.id == org_id))
    return result.scalar_one_or_none()


async def get_default_project(db: AsyncSession, org_id: str) -> models.Project | None:
    result = await db.execute(
        select(models.Project).where(models.Project.org_id == org_id, models.Project.name == "default")
    )
    return result.scalar_one_or_none()
