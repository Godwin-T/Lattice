from __future__ import annotations

from pydantic import BaseModel


class UsageOverviewResponse(BaseModel):
    total_requests: int
    total_cost_usd: float
    total_tokens: int
    avg_latency_ms: float


class UsageByUserItem(BaseModel):
    user_id: str | None
    email: str | None
    requests: int
    cost_usd: float
    tokens: int
    avg_latency_ms: float


class UsageByUserResponse(BaseModel):
    items: list[UsageByUserItem]


class UsageByProjectItem(BaseModel):
    project_id: str
    project_name: str
    requests: int
    cost_usd: float
    tokens: int
    avg_latency_ms: float


class UsageByProjectResponse(BaseModel):
    items: list[UsageByProjectItem]


class UsageByKeyItem(BaseModel):
    api_key_id: str
    key_prefix: str
    owner_user_id: str | None
    requests: int
    cost_usd: float
    tokens: int
    avg_latency_ms: float


class UsageByKeyResponse(BaseModel):
    items: list[UsageByKeyItem]
