from __future__ import annotations

from pydantic import BaseModel


class ProjectResponse(BaseModel):
    id: str
    org_id: str
    name: str


class ProjectCreateRequest(BaseModel):
    name: str


class ProjectUpdateRequest(BaseModel):
    name: str
