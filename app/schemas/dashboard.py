from __future__ import annotations

from pydantic import BaseModel


class TrendPoint(BaseModel):
    date: str
    value: float


class OverviewResponse(BaseModel):
    total_requests: int
    success_rate: float
    total_cost_usd: float
    avg_latency_ms: float
    trend: list[TrendPoint]


class UsagePoint(BaseModel):
    date: str
    tokens: int
    cost_usd: float


class ProviderBreakdown(BaseModel):
    provider: str
    requests: int
    cost_usd: float


class UsageResponse(BaseModel):
    by_day: list[UsagePoint]
    provider_breakdown: list[ProviderBreakdown]


class RequestItem(BaseModel):
    id: str
    created_at: str
    provider: str
    model: str
    status: int
    latency_ms: int
    cost_usd: float


class RequestsResponse(BaseModel):
    items: list[RequestItem]


class ProviderItem(BaseModel):
    provider: str
    enabled: bool


class ProvidersResponse(BaseModel):
    providers: list[ProviderItem]
    rate_limit_rpm: int
