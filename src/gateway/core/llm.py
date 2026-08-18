# spec: SPEC-001
"""LLM adapter（详细设计 §4.13）。OpenAI / Anthropic / Null 可切换。"""
from __future__ import annotations

import os
from typing import Optional, Protocol

from ..exceptions import NoLLMConfiguredError
from .config import LLMConfig


class LLMProvider(Protocol):
    def complete(self, prompt: str, model: Optional[str] = None) -> str: ...


class NullProvider:
    """未配置 provider 时使用：抛出 → 触发确定性模板回退。"""

    def complete(self, prompt: str, model: Optional[str] = None) -> str:
        raise NoLLMConfiguredError("no LLM provider configured")


class OpenAIProvider:
    def __init__(self, api_key_env: str = "OPENAI_API_KEY", model: str = ""):
        self._model = model
        self._api_key = os.environ.get(api_key_env, "")
        if not self._api_key:
            raise NoLLMConfiguredError(f"env {api_key_env} not set")
        import openai  # 懒加载

        self._client = openai.OpenAI(api_key=self._api_key)

    def complete(self, prompt: str, model: Optional[str] = None) -> str:
        resp = self._client.chat.completions.create(
            model=model or self._model or "gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.choices[0].message.content or ""


class AnthropicProvider:
    def __init__(self, api_key_env: str = "ANTHROPIC_API_KEY", model: str = ""):
        self._model = model
        self._api_key = os.environ.get(api_key_env, "")

    def complete(self, prompt: str, model: Optional[str] = None) -> str:
        if not self._api_key:
            raise NoLLMConfiguredError("ANTHROPIC_API_KEY not set")
        try:
            import anthropic  # 懒加载
        except ImportError:
            raise NoLLMConfiguredError("anthropic SDK not installed") from None
        client = anthropic.Anthropic(api_key=self._api_key)
        msg = client.messages.create(
            model=model or self._model or "claude-haiku-4-5",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")


def make_provider(cfg: LLMConfig) -> LLMProvider:
    """按配置构造 provider；none / 未知 → NullProvider。"""
    if cfg.provider == "openai":
        try:
            return OpenAIProvider(cfg.api_key_env, cfg.model)
        except NoLLMConfiguredError:
            return NullProvider()
    if cfg.provider == "anthropic":
        return AnthropicProvider(cfg.api_key_env, cfg.model)
    return NullProvider()
