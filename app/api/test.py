from __future__ import annotations

import time
import structlog
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_api_key, get_provider_router_dep, get_rate_limiter
from app.core.settings import get_settings
from app.db import models
from app.db.session import get_db
from app.schemas.openai import ChatCompletionRequest
from app.schemas.test import CompareTestRequest, CompareTestResponse, ProviderTestResult
from app.services.pricing import compute_chat_cost, pick_model_for_provider
from app.services.providers.base import ProviderError
from app.services.providers.router import ProviderRouter


router = APIRouter(prefix="/test", tags=["test"])
logger = structlog.get_logger()
settings = get_settings()


def _enabled_providers() -> set[str]:
    enabled: set[str] = set()
    if settings.openai_api_key:
        enabled.add("openai")
    if settings.groq_api_key:
        enabled.add("groq")
    if settings.anthropic_api_key:
        enabled.add("anthropic")
    return enabled


def _default_model_for(provider: str) -> str | None:
    if provider == "openai":
        return settings.openai_default_model
    if provider == "groq":
        return settings.groq_default_model
    if provider == "anthropic":
        return settings.anthropic_default_model
    return None


def _extract_usage(response: dict) -> tuple[int, int, int]:
    usage = response.get("usage") or {}
    prompt_tokens = usage.get("prompt_tokens") or 0
    completion_tokens = usage.get("completion_tokens") or 0
    total_tokens = usage.get("total_tokens") or (prompt_tokens + completion_tokens)
    return int(prompt_tokens), int(completion_tokens), int(total_tokens)


@router.post("/compare", response_model=CompareTestResponse)
async def compare_models(
    payload: CompareTestRequest,
    api_key: models.APIKey = Depends(get_current_api_key),
    provider_router: ProviderRouter = Depends(get_provider_router_dep),
    rate_limiter=Depends(get_rate_limiter),
    db: AsyncSession = Depends(get_db),
):
    del api_key

    enabled = _enabled_providers()
    if not enabled:
        return CompareTestResponse(items=[])

    items: list[ProviderTestResult] = []

    for item in payload.providers:
        provider = item.provider.lower()
        if provider not in enabled:
            continue

        model_for_provider = await pick_model_for_provider(db, provider, "chat", item.model)
        if not model_for_provider:
            model_for_provider = _default_model_for(provider)
        if not model_for_provider:
            continue

        start = time.perf_counter()
        try:
            allowed, _ = await rate_limiter.allow(f"rl:test:{provider}")
        except Exception as exc:
            logger.warning("test_rate_limiter_unavailable", error=str(exc))
            allowed = True

        if not allowed:
            items.append(
                ProviderTestResult(
                    provider=provider,
                    model=model_for_provider,
                    status="rate_limited",
                    latency_ms=0,
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0,
                    cost_usd=0.0,
                    response=None,
                    error_message="Rate limit exceeded",
                )
            )
            continue

        try:
            request_payload = ChatCompletionRequest(
                model=model_for_provider,
                provider=provider,
                messages=[{"role": "user", "content": payload.prompt}],
            )
            client = provider_router.get(provider)
            response = await client.chat(request_payload)
            latency_ms = int((time.perf_counter() - start) * 1000)
            prompt_tokens, completion_tokens, total_tokens = _extract_usage(response)
            cost_usd = await compute_chat_cost(db, provider, model_for_provider, prompt_tokens, completion_tokens)
            content = response.get("choices", [{}])[0].get("message", {}).get("content")
            items.append(
                ProviderTestResult(
                    provider=provider,
                    model=model_for_provider,
                    status="ok",
                    latency_ms=latency_ms,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    cost_usd=cost_usd,
                    response=content,
                    error_message=None,
                )
            )
        except ProviderError as exc:
            latency_ms = int((time.perf_counter() - start) * 1000)
            items.append(
                ProviderTestResult(
                    provider=provider,
                    model=model_for_provider,
                    status="error",
                    latency_ms=latency_ms,
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0,
                    cost_usd=0.0,
                    response=None,
                    error_message=exc.message,
                )
            )

    return CompareTestResponse(items=items)
