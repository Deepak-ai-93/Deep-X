from abc import ABC, abstractmethod
from typing import Optional
import logging

from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

from app.config import settings

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, model: Optional[str] = None) -> str:
        ...


class OpenAIProvider(LLMProvider):
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

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
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def generate(self, prompt: str, model: Optional[str] = None) -> str:
        resp = await self.client.messages.create(
            model=model or "claude-sonnet-4-20250514",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2048,
        )
        return resp.content[0].text if resp.content else ""


class OpenRouterProvider(LLMProvider):
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
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
            case "openai":
                _providers[name] = OpenAIProvider()
            case "anthropic":
                _providers[name] = AnthropicProvider()
            case "openrouter":
                _providers[name] = OpenRouterProvider()
            case _:
                raise ValueError(f"Unknown provider: {name}")
    return _providers[name]
