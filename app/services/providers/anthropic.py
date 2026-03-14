from __future__ import annotations

import time
from typing import Any, List

from anthropic import AsyncAnthropic

from app.core.settings import get_settings
from app.schemas.openai import ChatCompletionRequest, ChatMessage
from app.services.providers.base import ProviderError


settings = get_settings()


class AnthropicProvider:
    def __init__(self) -> None:
        if not settings.anthropic_api_key:
            raise ProviderError("Anthropic API key not configured", status_code=500)
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key, timeout=settings.request_timeout_s)

    async def chat(self, request: ChatCompletionRequest) -> dict:
        system, messages = _to_anthropic_messages(request.messages)
        if not messages:
            raise ProviderError("No valid messages provided", status_code=400, error_type="invalid_request_error")
        max_tokens = request.max_tokens or 1024
        try:
            resp = await self.client.messages.create(
                model=request.model,
                system=system or None,
                messages=messages,
                max_tokens=max_tokens,
                temperature=request.temperature,
            )
        except Exception as exc:
            status = getattr(exc, "status_code", 502)
            code = getattr(exc, "code", None)
            raise ProviderError(str(exc), status_code=status, error_type="provider_error", code=code) from exc

        content_text = _extract_content_text(resp.content)
        created = int(time.time())
        prompt_tokens = getattr(resp.usage, "input_tokens", 0) or 0
        completion_tokens = getattr(resp.usage, "output_tokens", 0) or 0
        return {
            "id": f"chatcmpl-{resp.id}",
            "object": "chat.completion",
            "created": created,
            "model": request.model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": content_text},
                    "finish_reason": getattr(resp, "stop_reason", None),
                }
            ],
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
        }

    async def embeddings(self, request: Any) -> dict:
        raise ProviderError("Anthropic embeddings are not supported", status_code=400, error_type="invalid_request_error")


def _normalize_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: List[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and "text" in item:
                parts.append(str(item["text"]))
        return "\n".join(parts)
    return str(content)


def _to_anthropic_messages(messages: List[ChatMessage]) -> tuple[str, list[dict]]:
    system_parts: List[str] = []
    converted: list[dict] = []
    for message in messages:
        if message.role == "system":
            system_parts.append(_normalize_content(message.content))
            continue
        if message.role not in {"user", "assistant"}:
            raise ProviderError(f"Unsupported message role: {message.role}", status_code=400, error_type="invalid_request_error")
        converted.append({"role": message.role, "content": _normalize_content(message.content)})
    return "\n".join(system_parts), converted


def _extract_content_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: List[str] = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
            elif hasattr(block, "text"):
                parts.append(getattr(block, "text"))
        return "\n".join(parts)
    return str(content)
