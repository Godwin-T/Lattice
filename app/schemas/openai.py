from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict


class ChatMessage(BaseModel):
    role: str
    content: Any
    name: Optional[str] = None


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    provider: Optional[str] = None
    fallback: Optional[bool] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False

    model_config = ConfigDict(extra="allow")


class EmbeddingsRequest(BaseModel):
    model: str
    input: Any
    provider: Optional[str] = None
    fallback: Optional[bool] = None
    encoding_format: Optional[str] = None
    dimensions: Optional[int] = None

    model_config = ConfigDict(extra="allow")
