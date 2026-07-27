from __future__ import annotations

from typing import Any, Protocol

from langchain_core.messages import BaseMessage


class LLMRuntime(Protocol):
    """Provider runtime abstraction used by agent orchestration code."""

    def create_chat_model(
        self,
        *,
        model: str,
        reasoning_effort: str,
        verbosity: str | None,
        max_tokens: int,
    ) -> Any:
        """Create a chat model instance for the provider."""

    def build_preamble(
        self,
        *,
        prompt: str,
    ) -> list[BaseMessage]:
        """Build provider-specific instruction preamble messages."""

    def prepare_tools(self, tools: list) -> tuple[list, list]:
        """Return (llm_tools, node_tools) after provider-specific mapping."""

    def bind_reasoning(self, llm: Any, *, reasoning_effort: str, adaptive: bool = True) -> Any:
        """Bind request-scoped reasoning controls."""

    def bind_reasoning_trace(self, llm: Any) -> Any:
        """Bind request options needed for encrypted reasoning traces."""

    def invoke(
        self,
        llm: Any,
        messages: list[BaseMessage],
        *,
        reasoning_effort: str | None = None,
    ) -> Any:
        """Invoke a model with provider-specific call arguments."""

    def with_structured_output(
        self,
        llm: Any,
        schema: Any,
        *,
        include_raw: bool,
        strict: bool | None = None,
        tools: list | None = None,
        include_reasoning_trace: bool = False,
        reasoning_effort: str | None = None,
    ) -> Any:
        """Create a structured-output bound model with provider-specific args."""
