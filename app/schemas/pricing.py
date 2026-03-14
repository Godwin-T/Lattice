from __future__ import annotations

from pydantic import BaseModel, Field


class ModelPricingBase(BaseModel):
    provider: str
    model: str
    model_type: str
    cost_per_1m_tokens: float = Field(ge=0)
    active: bool = True


class ModelPricingCreateRequest(ModelPricingBase):
    pass


class ModelPricingUpdateRequest(BaseModel):
    provider: str | None = None
    model: str | None = None
    model_type: str | None = None
    cost_per_1m_tokens: float | None = Field(default=None, ge=0)
    active: bool | None = None


class ModelPricingResponse(ModelPricingBase):
    id: str
    updated_at: str
    created_at: str
