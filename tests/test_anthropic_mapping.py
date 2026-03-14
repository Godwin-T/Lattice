from app.schemas.openai import ChatMessage
from app.services.providers.anthropic import _to_anthropic_messages


def test_to_anthropic_messages_system_and_user():
    messages = [
        ChatMessage(role="system", content="sys"),
        ChatMessage(role="user", content="hi"),
        ChatMessage(role="assistant", content="hello"),
    ]
    system, converted = _to_anthropic_messages(messages)
    assert system == "sys"
    assert converted == [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
    ]
