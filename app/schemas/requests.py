from __future__ import annotations

from pydantic import BaseModel


class RequestLogItem(BaseModel):
    id: str
    created_at: str
    org_id: str | None
    project_id: str
    api_key_id: str | None
    owner_user_id: str | None
    provider: str
    model: str
    status: int
    latency_ms: int
    cost_usd: float


class RequestLogResponse(BaseModel):
    items: list[RequestLogItem]
