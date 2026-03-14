from __future__ import annotations

from pydantic import BaseModel, Field


class ProviderTestRequest(BaseModel):
    provider: str
    model: str


class CompareTestRequest(BaseModel):
    prompt: str = Field(min_length=1)
    providers: list[ProviderTestRequest]
    fallback: bool | None = None


class ProviderTestResult(BaseModel):
    provider: str
    model: str
    status: str
    latency_ms: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    response: str | None = None
    error_message: str | None = None


class CompareTestResponse(BaseModel):
    items: list[ProviderTestResult]
