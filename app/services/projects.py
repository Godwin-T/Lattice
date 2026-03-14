from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import models


async def ensure_default_project(db: AsyncSession, org_id: str) -> models.Project:
    result = await db.execute(
        select(models.Project).where(models.Project.org_id == org_id, models.Project.name == "default")
    )
    project = result.scalar_one_or_none()
    if project:
        return project
    project = models.Project(org_id=org_id, name="default")
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project
