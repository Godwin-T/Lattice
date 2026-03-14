from __future__ import annotations

from functools import lru_cache

from app.core.settings import get_settings
from app.services.providers.anthropic import AnthropicProvider
from app.services.providers.base import ProviderClient, ProviderError
from app.services.providers.groq import GroqProvider
from app.services.providers.openai import OpenAIProvider


class ProviderRouter:
    def __init__(self) -> None:
        self._clients: dict[str, ProviderClient] = {}

    def get(self, provider: str) -> ProviderClient:
        provider = provider.lower()
        if provider in self._clients:
            return self._clients[provider]
        if provider == "openai":
            self._clients[provider] = OpenAIProvider()
        elif provider == "anthropic":
            self._clients[provider] = AnthropicProvider()
        elif provider == "groq":
            self._clients[provider] = GroqProvider()
        else:
            raise ProviderError(f"Unsupported provider: {provider}", status_code=400, error_type="invalid_request_error")
        return self._clients[provider]


@lru_cache
def get_provider_router() -> ProviderRouter:
    _ = get_settings()
    return ProviderRouter()
