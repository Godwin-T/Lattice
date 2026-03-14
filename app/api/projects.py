from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_membership, require_admin
from app.db import models
from app.db.session import get_db
from app.schemas.projects import ProjectCreateRequest, ProjectResponse, ProjectUpdateRequest


router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectResponse])
async def list_projects(membership=Depends(get_current_membership), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Project).where(models.Project.org_id == membership.org_id))
    return [ProjectResponse(id=p.id, org_id=p.org_id, name=p.name) for p in result.scalars().all()]


@router.post("", response_model=ProjectResponse)
async def create_project(
    payload: ProjectCreateRequest,
    membership=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    project = models.Project(org_id=membership.org_id, name=payload.name)
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return ProjectResponse(id=project.id, org_id=project.org_id, name=project.name)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    payload: ProjectUpdateRequest,
    membership=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(models.Project).where(models.Project.id == project_id, models.Project.org_id == membership.org_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project.name = payload.name
    await db.commit()
    return ProjectResponse(id=project.id, org_id=project.org_id, name=project.name)
