from abc import ABC, abstractmethod
from typing import Optional
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, model: Optional[str] = None) -> str:
        ...


class NoopProvider(LLMProvider):
    async def generate(self, prompt: str, model: Optional[str] = None) -> str:
        logger.warning("No AI provider configured. Returning empty response.")
        return ""


class OpenAIProvider(LLMProvider):
    def __init__(self):
        from openai import AsyncOpenAI
        from app.config import settings as s
        if not s.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY not set")
        self.client = AsyncOpenAI(api_key=s.openai_api_key)

    async def generate(self, prompt: str, model: Optional[str] = None) -> str:
        resp = await self.client.chat.completions.create(
            model=model or "gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2048,
        )
        return resp.choices[0].message.content or ""


class AnthropicProvider(LLMProvider):
    def __init__(self):
        from anthropic import AsyncAnthropic
        from app.config import settings as s
        if not s.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set")
        self.client = AsyncAnthropic(api_key=s.anthropic_api_key)

    async def generate(self, prompt: str, model: Optional[str] = None) -> str:
        resp = await self.client.messages.create(
            model=model or "claude-sonnet-4-20250514",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2048,
        )
        return resp.content[0].text if resp.content else ""


class OpenRouterProvider(LLMProvider):
    def __init__(self):
        from openai import AsyncOpenAI
        from app.config import settings as s
        if not s.openrouter_api_key:
            raise RuntimeError("OPENROUTER_API_KEY not set")
        self.client = AsyncOpenAI(
            api_key=s.openrouter_api_key,
            base_url=s.openrouter_base_url,
        )

    async def generate(self, prompt: str, model: Optional[str] = None) -> str:
        resp = await self.client.chat.completions.create(
            model=model or "openai/gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2048,
        )
        return resp.choices[0].message.content or ""


_providers: dict[str, LLMProvider] = {}


def get_provider(name: Optional[str] = None) -> LLMProvider:
    name = name or settings.default_provider
    if name not in _providers:
        match name:
            case "noop":
                _providers[name] = NoopProvider()
            case "openai":
                _providers[name] = OpenAIProvider()
            case "anthropic":
                _providers[name] = AnthropicProvider()
            case "openrouter":
                _providers[name] = OpenRouterProvider()
            case _:
                raise ValueError(f"Unknown provider: {name}")
    return _providers[name]
