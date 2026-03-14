from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_membership
from app.db import models
from app.db.session import get_db
from app.schemas.orgs import OrgResponse


router = APIRouter(prefix="/orgs", tags=["orgs"])


@router.get("/me", response_model=OrgResponse)
async def get_org(membership=Depends(get_current_membership), db: AsyncSession = Depends(get_db)):
    org = await db.get(models.Org, membership.org_id)
    return OrgResponse(id=org.id, name=org.name)
