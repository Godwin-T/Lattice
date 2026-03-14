from __future__ import annotations

from typing import Any

from openai import AsyncOpenAI

from app.core.settings import get_settings
from app.schemas.openai import ChatCompletionRequest, EmbeddingsRequest
from app.services.providers.base import ProviderError


settings = get_settings()

DEFAULT_GROQ_BASE_URL = "https://api.groq.com/openai/v1"


class GroqProvider:
    def __init__(self) -> None:
        if not settings.groq_api_key:
            raise ProviderError("Groq API key not configured", status_code=500)
        base_url = settings.groq_base_url or DEFAULT_GROQ_BASE_URL
        self.client = AsyncOpenAI(
            api_key=settings.groq_api_key,
            base_url=base_url,
            timeout=settings.request_timeout_s,
        )

    async def chat(self, request: ChatCompletionRequest) -> dict:
        if request.stream:
            raise ProviderError("Streaming is not supported in this gateway", status_code=400, error_type="invalid_request_error")
        payload = request.model_dump(exclude={"provider", "fallback"}, exclude_none=True)
        payload.pop("stream", None)
        try:
            resp = await self.client.chat.completions.create(**payload)
            return _to_dict(resp)
        except Exception as exc:
            status = getattr(exc, "status_code", 502)
            code = getattr(exc, "code", None)
            raise ProviderError(str(exc), status_code=status, error_type="provider_error", code=code) from exc

    async def embeddings(self, request: EmbeddingsRequest) -> dict:
        payload = request.model_dump(exclude={"provider", "fallback"}, exclude_none=True)
        try:
            resp = await self.client.embeddings.create(**payload)
            return _to_dict(resp)
        except Exception as exc:
            status = getattr(exc, "status_code", 502)
            code = getattr(exc, "code", None)
            raise ProviderError(str(exc), status_code=status, error_type="provider_error", code=code) from exc


def _to_dict(response: Any) -> dict:
    if hasattr(response, "model_dump"):
        return response.model_dump()
    if hasattr(response, "dict"):
        return response.dict()
    return dict(response)
