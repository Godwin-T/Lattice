from __future__ import annotations

from pydantic import BaseModel


class OrgResponse(BaseModel):
    id: str
    name: str
