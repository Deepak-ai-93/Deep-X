from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    database_url: str = "sqlite+aiosqlite:///./viral_content.db"

    x402_secret: Optional[str] = None
    x402_enabled: bool = True

    api_key_header: str = "X-API-Key"
    rate_limit_requests: int = 60
    rate_limit_window: int = 60

    log_level: str = "INFO"
    environment: str = "development"

    otlp_endpoint: Optional[str] = None
    service_name: str = "viral-content-mcp"

    host: str = "0.0.0.0"
    port: int = 10000
    workers: int = 1

    default_provider: str = "noop"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
