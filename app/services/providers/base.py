from __future__ import annotations

from typing import Protocol

from app.schemas.openai import ChatCompletionRequest, EmbeddingsRequest


class ProviderError(Exception):
    def __init__(self, message: str, status_code: int = 500, error_type: str = "provider_error", code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_type = error_type
        self.code = code


class ProviderClient(Protocol):
    async def chat(self, request: ChatCompletionRequest) -> dict:
        ...

    async def embeddings(self, request: EmbeddingsRequest) -> dict:
        ...
