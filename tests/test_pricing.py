from app.core.pricing import compute_chat_cost, compute_embedding_cost


def test_compute_chat_cost():
    cost = compute_chat_cost("openai", "gpt-4o-mini", 1000, 1000)
    assert cost > 0


def test_compute_embedding_cost():
    cost = compute_embedding_cost("openai", "text-embedding-3-small", 1000)
    assert cost > 0
