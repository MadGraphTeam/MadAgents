from __future__ import annotations

from madagents.llm.anthropic_runtime import AnthropicLLMRuntime
from madagents.llm.openai_runtime import OpenAILLMRuntime
from madagents.llm.runtime import LLMRuntime

_DEFAULT_RUNTIME: LLMRuntime = OpenAILLMRuntime()


def get_default_runtime() -> LLMRuntime:
    """Return the default provider runtime (OpenAI for now)."""
    return _DEFAULT_RUNTIME


def get_runtime_for_provider(provider: str) -> LLMRuntime:
    """Return a runtime instance for a named provider."""
    normalized = (provider or "").strip().lower()
    if normalized == "anthropic":
        return AnthropicLLMRuntime()
    return OpenAILLMRuntime()
