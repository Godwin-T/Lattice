import pytest

from app.services.providers.groq import GroqProvider
from app.services.providers.base import ProviderError


@pytest.mark.asyncio
async def test_groq_missing_key():
    with pytest.raises(ProviderError):
        GroqProvider()
