from __future__ import annotations

import time

import structlog
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_api_key, get_provider_router_dep, get_rate_limiter
from app.core.settings import get_settings
from app.db import models
from app.db.session import get_db
from app.observability.metrics import record_rate_limit, record_request
from app.schemas.errors import OpenAIError
from app.schemas.openai import ChatCompletionRequest, EmbeddingsRequest
from app.services.pricing import compute_chat_cost, compute_embedding_cost, pick_model_for_provider
from app.services.providers.base import ProviderError
from app.services.providers.router import ProviderRouter
from app.services.request_logging import log_request


router = APIRouter()
logger = structlog.get_logger()
settings = get_settings()

def _pick_initial_provider(requested: str | None, enabled: set[str]) -> str:
    if requested:
        req = requested.lower()
        if req in enabled:
            return req
    order = settings.fallback_order_list()
    for provider in order:
        if provider in enabled:
            return provider
    return next(iter(enabled))

def _extract_usage(response: dict) -> tuple[int, int, int]:
    usage = response.get("usage") or {}
    prompt_tokens = usage.get("prompt_tokens") or 0
    completion_tokens = usage.get("completion_tokens") or 0
    total_tokens = usage.get("total_tokens") or (prompt_tokens + completion_tokens)
    return int(prompt_tokens), int(completion_tokens), int(total_tokens)


def _should_fallback(exc: ProviderError) -> bool:
    if exc.status_code in {401, 403, 408}:
        return True
    return exc.status_code >= 500


def _fallback_enabled(flag: bool | None) -> bool:
    return settings.fallback_enabled_default if flag is None else bool(flag)


def _provider_candidates(primary: str, fallback_enabled: bool) -> list[str]:
    candidates: list[str] = [primary]
    if fallback_enabled:
        for provider in settings.fallback_order_list():
            if provider not in candidates:
                candidates.append(provider)
    return candidates


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


@router.post("/v1/chat/completions")
async def chat_completions(
    request: Request,
    payload: ChatCompletionRequest,
    api_key: models.APIKey = Depends(get_current_api_key),
    provider_router: ProviderRouter = Depends(get_provider_router_dep),
    rate_limiter=Depends(get_rate_limiter),
    db: AsyncSession = Depends(get_db),
):
    start = time.perf_counter()
    provider = (payload.provider or "").lower() or None
    if payload.stream:
        raise OpenAIError("Streaming is not supported", status_code=400)

    status_code = 500
    error_code = None
    error_message = None
    prompt_tokens = completion_tokens = total_tokens = 0
    cost_usd = 0.0

    try:
        allowed, _ = await rate_limiter.allow(f"rl:{api_key.id}")
    except Exception as exc:
        raise OpenAIError("Rate limiter unavailable", status_code=503, error_type="service_unavailable") from exc

    if not allowed:
        record_rate_limit("chat")
        raise OpenAIError("Rate limit exceeded", status_code=429, error_type="rate_limit_error")

    enabled_providers = _enabled_providers()
    if not enabled_providers:
        raise OpenAIError(
            "No provider API keys configured. Set OPENAI_API_KEY, GROQ_API_KEY, or ANTHROPIC_API_KEY.",
            status_code=503,
            error_type="service_unavailable",
        )

    used_provider = provider or ""
    model_used = payload.model
    fallback_used = False
    last_error: ProviderError | None = None
    try:
        fallback_enabled = _fallback_enabled(payload.fallback)
        primary = _pick_initial_provider(provider, enabled_providers)
        for candidate in _provider_candidates(primary, fallback_enabled):
            if candidate not in enabled_providers:
                continue
            try:
                model_for_provider = await pick_model_for_provider(db, candidate, "chat", payload.model)
                if not model_for_provider:
                    model_for_provider = _default_model_for(candidate)
                if not model_for_provider:
                    continue
                request_payload = payload.model_copy(update={"model": model_for_provider})
                client = provider_router.get(candidate)
                response = await client.chat(request_payload)
                used_provider = candidate
                model_used = model_for_provider
                fallback_used = candidate != primary
                prompt_tokens, completion_tokens, total_tokens = _extract_usage(response)
                cost_usd = await compute_chat_cost(db, used_provider, model_for_provider, prompt_tokens, completion_tokens)
                status_code = 200
                error_code = None
                error_message = None
                last_error = None
                break
            except ProviderError as exc:
                last_error = exc
                if not fallback_enabled or not _should_fallback(exc):
                    raise
                continue
        if status_code != 200:
            if last_error is not None:
                raise last_error
            raise OpenAIError(
                "No enabled providers available for request.",
                status_code=503,
                error_type="service_unavailable",
            )
    except ProviderError as exc:
        status_code = exc.status_code
        response = None
        prompt_tokens = completion_tokens = total_tokens = 0
        cost_usd = 0.0
        error_code = exc.code
        error_message = exc.message
        raise OpenAIError(exc.message, status_code=exc.status_code, error_type=exc.error_type, code=exc.code) from exc
    finally:
        latency_ms = int((time.perf_counter() - start) * 1000)
        record_request("chat", used_provider, status_code, latency_ms / 1000.0)
        try:
            project_id = api_key.project_id
            org_id = api_key.project.org_id if api_key.project else None
            await log_request(
                db,
                org_id=org_id,
                project_id=project_id,
                api_key_id=api_key.id,
                owner_user_id=api_key.owner_user_id,
                provider=used_provider,
                model=model_used,
                endpoint="chat",
                status=status_code,
                latency_ms=latency_ms,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cost_usd=cost_usd,
                error_code=error_code,
                error_message=error_message,
            )
        except Exception as exc:
            logger.warning("request_log_failed", error=str(exc))

    response_obj = JSONResponse(content=response)
    request_id = getattr(request.state, "request_id", None)
    if request_id:
        response_obj.headers["X-Request-ID"] = request_id
    response_obj.headers["X-Provider-Used"] = used_provider
    response_obj.headers["X-Provider-Fallback"] = "true" if fallback_used else "false"
    return response_obj


@router.post("/v1/embeddings")
async def embeddings(
    request: Request,
    payload: EmbeddingsRequest,
    api_key: models.APIKey = Depends(get_current_api_key),
    provider_router: ProviderRouter = Depends(get_provider_router_dep),
    rate_limiter=Depends(get_rate_limiter),
    db: AsyncSession = Depends(get_db),
):
    start = time.perf_counter()
    provider = (payload.provider or "").lower() or None

    status_code = 500
    error_code = None
    error_message = None
    prompt_tokens = completion_tokens = total_tokens = 0
    cost_usd = 0.0

    try:
        allowed, _ = await rate_limiter.allow(f"rl:{api_key.id}")
    except Exception as exc:
        raise OpenAIError("Rate limiter unavailable", status_code=503, error_type="service_unavailable") from exc

    if not allowed:
        record_rate_limit("embeddings")
        raise OpenAIError("Rate limit exceeded", status_code=429, error_type="rate_limit_error")

    enabled_providers = _enabled_providers()
    if not enabled_providers:
        raise OpenAIError(
            "No provider API keys configured. Set OPENAI_API_KEY, GROQ_API_KEY, or ANTHROPIC_API_KEY.",
            status_code=503,
            error_type="service_unavailable",
        )

    used_provider = provider or ""
    fallback_used = False
    last_error: ProviderError | None = None
    try:
        fallback_enabled = _fallback_enabled(payload.fallback)
        primary = _pick_initial_provider(provider, enabled_providers)
        for candidate in _provider_candidates(primary, fallback_enabled):
            if candidate not in enabled_providers:
                continue
            try:
                model_for_provider = await pick_model_for_provider(db, candidate, "embedding", payload.model)
                if not model_for_provider:
                    continue
                request_payload = payload.model_copy(update={"model": model_for_provider})
                client = provider_router.get(candidate)
                response = await client.embeddings(request_payload)
                used_provider = candidate
                model_used = model_for_provider
                fallback_used = candidate != primary
                prompt_tokens, completion_tokens, total_tokens = _extract_usage(response)
                cost_usd = await compute_embedding_cost(db, used_provider, model_for_provider, total_tokens or prompt_tokens)
                status_code = 200
                error_code = None
                error_message = None
                last_error = None
                break
            except ProviderError as exc:
                last_error = exc
                if not fallback_enabled or not _should_fallback(exc):
                    raise
                continue
        if status_code != 200:
            if last_error is not None:
                raise last_error
            raise OpenAIError(
                "No enabled providers available for request.",
                status_code=503,
                error_type="service_unavailable",
            )
    except ProviderError as exc:
        status_code = exc.status_code
        response = None
        prompt_tokens = completion_tokens = total_tokens = 0
        cost_usd = 0.0
        error_code = exc.code
        error_message = exc.message
        raise OpenAIError(exc.message, status_code=exc.status_code, error_type=exc.error_type, code=exc.code) from exc
    finally:
        latency_ms = int((time.perf_counter() - start) * 1000)
        record_request("embeddings", used_provider, status_code, latency_ms / 1000.0)
        try:
            project_id = api_key.project_id
            org_id = api_key.project.org_id if api_key.project else None
            await log_request(
                db,
                org_id=org_id,
                project_id=project_id,
                api_key_id=api_key.id,
                owner_user_id=api_key.owner_user_id,
                provider=used_provider,
                model=model_used,
                endpoint="embeddings",
                status=status_code,
                latency_ms=latency_ms,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cost_usd=cost_usd,
                error_code=error_code,
                error_message=error_message,
            )
        except Exception as exc:
            logger.warning("request_log_failed", error=str(exc))

    response_obj = JSONResponse(content=response)
    request_id = getattr(request.state, "request_id", None)
    if request_id:
        response_obj.headers["X-Request-ID"] = request_id
    response_obj.headers["X-Provider-Used"] = used_provider
    response_obj.headers["X-Provider-Fallback"] = "true" if fallback_used else "false"
    return response_obj
