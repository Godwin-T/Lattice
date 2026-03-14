from __future__ import annotations

from typing import Optional

PRICING = {
    "openai": {
        "gpt-4o": {"prompt": 0.005, "completion": 0.015},
        "gpt-4o-mini": {"prompt": 0.00015, "completion": 0.0006},
        "gpt-3.5-turbo": {"prompt": 0.0005, "completion": 0.0015},
        "text-embedding-3-small": {"embedding": 0.00002},
        "text-embedding-3-large": {"embedding": 0.00013},
    },
    "anthropic": {
        "claude-3-5-sonnet": {"prompt": 0.003, "completion": 0.015},
        "claude-3-5-haiku": {"prompt": 0.00025, "completion": 0.00125},
    },
    "groq": {
        "llama-3.1-70b-versatile": {"prompt": 0.0, "completion": 0.0},
        "llama-3.1-8b-instant": {"prompt": 0.0, "completion": 0.0},
        "mixtral-8x7b-32768": {"prompt": 0.0, "completion": 0.0},
    },
}


def _cost_per_1k(provider: str, model: str, key: str) -> Optional[float]:
    model_pricing = PRICING.get(provider, {}).get(model)
    if not model_pricing:
        return None
    return model_pricing.get(key)


def compute_chat_cost(provider: str, model: str, prompt_tokens: int, completion_tokens: int) -> float:
    prompt_cost = _cost_per_1k(provider, model, "prompt")
    completion_cost = _cost_per_1k(provider, model, "completion")
    if prompt_cost is None or completion_cost is None:
        return 0.0
    return (prompt_tokens / 1000.0) * prompt_cost + (completion_tokens / 1000.0) * completion_cost


def compute_embedding_cost(provider: str, model: str, total_tokens: int) -> float:
    embedding_cost = _cost_per_1k(provider, model, "embedding")
    if embedding_cost is None:
        return 0.0
    return (total_tokens / 1000.0) * embedding_cost
