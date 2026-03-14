from __future__ import annotations

from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    environment: str = Field(default="dev", alias="ENVIRONMENT")
    service_name: str = Field(default="latticeai-gateway", alias="SERVICE_NAME")
    api_key_secret: str = Field(default="change-me", alias="API_KEY_SECRET")

    database_url: str = Field(default="postgresql+asyncpg://lattice:lattice@localhost:5432/lattice", alias="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    rate_limit_rpm: int = Field(default=60, alias="RATE_LIMIT_RPM")

    request_timeout_s: float = Field(default=30, alias="REQUEST_TIMEOUT_S")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    groq_base_url: Optional[str] = Field(default=None, alias="GROQ_BASE_URL")

    session_secret: str = Field(default="change-me", alias="SESSION_SECRET")
    session_cookie_name: str = Field(default="lattice_session", alias="SESSION_COOKIE_NAME")
    session_ttl_hours: int = Field(default=24 * 7, alias="SESSION_TTL_HOURS")
    session_cookie_secure: bool = Field(default=False, alias="SESSION_COOKIE_SECURE")

    admin_email: str = Field(default="admin@lattice.com", alias="ADMIN_EMAIL")
    admin_password: str = Field(default="admin@lattice", alias="ADMIN_PASSWORD")
    admin_org_name: str = Field(default="lattice-org", alias="ADMIN_ORG_NAME")

    fallback_order: str = Field(default="openai,groq,anthropic", alias="FALLBACK_ORDER")
    fallback_enabled_default: bool = Field(default=True, alias="FALLBACK_ENABLED_DEFAULT")
    openai_default_model: str = Field(default="gpt-4o-mini", alias="OPENAI_DEFAULT_MODEL")
    groq_default_model: str = Field(default="llama-3.1-8b-instant", alias="GROQ_DEFAULT_MODEL")
    anthropic_default_model: str = Field(default="claude-3-5-haiku", alias="ANTHROPIC_DEFAULT_MODEL")

    otel_enabled: bool = Field(default=False, alias="OTEL_ENABLED")
    otel_exporter_otlp_endpoint: Optional[str] = Field(default=None, alias="OTEL_EXPORTER_OTLP_ENDPOINT")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    cors_origins: str = Field(default="http://localhost:5173,http://127.0.0.1:5173", alias="CORS_ORIGINS")

    def cors_origin_list(self) -> List[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    def fallback_order_list(self) -> List[str]:
        return [item.strip().lower() for item in self.fallback_order.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
