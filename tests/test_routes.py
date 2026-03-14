import pytest

from app.api import deps
from app.main import app
from app.services.providers.base import ProviderClient


class DummyProvider(ProviderClient):
    async def chat(self, request):
        return {
            "id": "chatcmpl-test",
            "object": "chat.completion",
            "created": 0,
            "model": request.model,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": "ok"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        }

    async def embeddings(self, request):
        return {
            "object": "list",
            "data": [{"index": 0, "embedding": [0.1, 0.2]}],
            "model": request.model,
            "usage": {"total_tokens": 5},
        }


class DummyRouter:
    def get(self, provider: str):
        return DummyProvider()


class DummyRateLimiter:
    async def allow(self, key: str):
        return True, 1


@pytest.mark.asyncio
async def test_chat_completions(client, api_key):
    app.dependency_overrides[deps.get_provider_router_dep] = lambda: DummyRouter()
    app.dependency_overrides[deps.get_rate_limiter] = lambda: DummyRateLimiter()

    try:
        response = await client.post(
            "/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": "gpt-4o-mini",
                "provider": "openai",
                "messages": [{"role": "user", "content": "hi"}],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["choices"][0]["message"]["content"] == "ok"
    finally:
        app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_embeddings(client, api_key):
    app.dependency_overrides[deps.get_provider_router_dep] = lambda: DummyRouter()
    app.dependency_overrides[deps.get_rate_limiter] = lambda: DummyRateLimiter()

    try:
        response = await client.post(
            "/v1/embeddings",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": "text-embedding-3-small",
                "provider": "openai",
                "input": "hello",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"][0]["embedding"] == [0.1, 0.2]
    finally:
        app.dependency_overrides = {}
