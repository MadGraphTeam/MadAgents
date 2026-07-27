from __future__ import annotations

import os
from typing import Any

from langchain_core.messages import BaseMessage, SystemMessage

from madagents.llm.runtime import LLMRuntime
from madagents.tools import (
    anthropic_read_image_tool,
    anthropic_read_pdf_tool,
    anthropic_web_search_tool,
)

ANTHROPIC_DEFAULT_MAX_OUTPUT_TOKENS = 64_000
ANTHROPIC_OPUS_46_MAX_OUTPUT_TOKENS = 128_000

_ADAPTIVE_THINKING_MODELS = {"claude-opus-4-7", "claude-opus-4-6", "claude-sonnet-4-6"}


def _supports_adaptive_thinking(model: str) -> bool:
    """Check if model supports adaptive thinking (4.6 models)."""
    normalized = (model or "").strip().lower()
    return any(m in normalized for m in _ADAPTIVE_THINKING_MODELS)


def _map_effort_for_adaptive(reasoning_effort: str) -> str | None:
    """Map reasoning_effort to Anthropic effort level for adaptive thinking.

    Returns None if thinking should be disabled entirely.
    """
    effort = (reasoning_effort or "").strip().lower()
    if effort in {"", "minimal"}:
        return None  # Disable thinking entirely
    if effort == "low":
        return "low"
    if effort == "medium":
        return "medium"
    return "high"  # "high" or anything else


def _resolve_api_key(primary_env: str) -> str:
    primary = os.environ.get(primary_env, "").strip()
    if primary:
        return primary
    fallback = os.environ.get("LLM_API_KEY", "").strip()
    return fallback


def _thinking_for_effort(reasoning_effort: str, max_tokens: int) -> dict | None:
    effort = (reasoning_effort or "").strip().lower()
    if effort in {"", "low", "minimal"}:
        return None
    budget = 4096 if effort == "medium" else 16384
    if isinstance(max_tokens, int) and max_tokens > 1 and budget >= max_tokens:
        budget = max_tokens - 1
    if budget <= 0:
        return None
    return {"type": "enabled", "budget_tokens": budget}

def _cap_max_tokens(model: str, max_tokens: int) -> int:
    """Clamp max_tokens to provider limits for known Anthropic models."""
    if not isinstance(max_tokens, int) or max_tokens <= 0:
        return max_tokens
    if _supports_adaptive_thinking(model):
        return min(max_tokens, ANTHROPIC_OPUS_46_MAX_OUTPUT_TOKENS)
    normalized = (model or "").strip().lower()
    if normalized.startswith("claude-"):
        return min(max_tokens, ANTHROPIC_DEFAULT_MAX_OUTPUT_TOKENS)
    return max_tokens


def _get_inner_llm(llm: Any) -> Any:
    """Traverse RunnableBinding chain to reach the innermost model."""
    current = llm
    for _ in range(20):  # safety limit
        inner = getattr(current, "bound", None)
        if inner is None:
            break
        current = inner
    return current


def _build_strip_update(llm: Any) -> dict[str, Any]:
    """Build the update dict for stripping thinking from *llm*."""
    update: dict[str, Any] = {"thinking": None}
    model_kwargs = getattr(llm, "model_kwargs", None)
    if isinstance(model_kwargs, dict) and "output_config" in model_kwargs:
        update["model_kwargs"] = {
            k: v for k, v in model_kwargs.items() if k != "output_config"
        }
    return update


def _has_thinking_in_bind_kwargs(llm: Any) -> bool:
    """Check if any RunnableBinding in the chain carries ``thinking``."""
    current = llm
    while hasattr(current, "bound"):
        kw = getattr(current, "kwargs", None)
        if isinstance(kw, dict) and kw.get("thinking") is not None:
            return True
        current = current.bound
    return False


def _strip_thinking(llm: Any) -> Any:
    """Return the LLM with thinking disabled when possible.

    Handles three cases:

    1. ``thinking`` set on the ChatAnthropic constructor field (legacy).
       Uses ``model_copy`` when the LLM is unwrapped, mutation otherwise.
    2. ``thinking`` passed via ``.bind()`` (preferred approach).
       An outer ``.bind(thinking=None)`` overrides it in the kwargs chain.
    3. No thinking configured — returns *llm* unchanged.

    For Opus 4.6, also cleans up ``output_config`` from ``model_kwargs``.
    """
    inner = _get_inner_llm(llm)

    # Case 1: thinking on the constructor field.
    if getattr(inner, "thinking", None) is not None:
        update = _build_strip_update(inner)
        if llm is inner:
            for copier in ("model_copy", "copy"):
                fn = getattr(inner, copier, None)
                if callable(fn):
                    try:
                        return fn(update=update)
                    except TypeError:
                        try:
                            return fn(deep=True, update=update)
                        except Exception:
                            pass
                    except Exception:
                        pass
        # RunnableBinding — mutate inner as last resort.
        try:
            inner.thinking = None
            model_kwargs = getattr(inner, "model_kwargs", None)
            if isinstance(model_kwargs, dict):
                model_kwargs.pop("output_config", None)
        except Exception:
            pass
        return llm

    # Case 2: thinking lives in bind kwargs (self.thinking is None).
    if _has_thinking_in_bind_kwargs(llm):
        return llm.bind(thinking=None)

    return llm


def _get_model_name(llm: Any) -> str:
    """Extract model name from an LLM instance or RunnableBinding."""
    model = getattr(llm, "model", None)
    if model:
        return model
    for attr in ("first", "bound"):
        inner = getattr(llm, attr, None)
        if inner:
            m = getattr(inner, "model", None)
            if m:
                return m
    return ""


class AnthropicLLMRuntime(LLMRuntime):
    """Anthropic runtime implementation with thinking guardrails."""

    def create_chat_model(
        self,
        *,
        model: str,
        reasoning_effort: str,
        verbosity: str | None,
        max_tokens: int,
    ) -> Any:
        try:
            from langchain_anthropic import ChatAnthropic
        except Exception as exc:  # pragma: no cover - runtime import guard
            raise RuntimeError(
                "langchain_anthropic is required for AnthropicLLMRuntime."
            ) from exc

        api_key = _resolve_api_key("ANTHROPIC_API_KEY")
        capped_max_tokens = _cap_max_tokens(model, max_tokens)
        kwargs: dict[str, Any] = {
            "model": model,
            "api_key": api_key,
            "max_tokens": capped_max_tokens,
        }
        # NOTE: We intentionally do NOT set ``thinking`` on the constructor.
        # ChatAnthropic._get_request_payload always overwrites kwargs with
        # ``self.thinking`` when it is not None, which makes later
        # ``.bind(thinking=...)`` calls (used by bind_reasoning) ineffective.
        # By leaving ``self.thinking = None`` and passing thinking via
        # ``.bind()``, outer bindings can properly override inner ones.
        if _supports_adaptive_thinking(model):
            effort_level = _map_effort_for_adaptive(reasoning_effort)
            llm = ChatAnthropic(**kwargs)
            if effort_level is not None:
                llm = llm.bind(
                    thinking={"type": "adaptive"},
                    output_config={"effort": effort_level},
                )
            return llm
        thinking = _thinking_for_effort(reasoning_effort, capped_max_tokens)
        if thinking is not None:
            kwargs["default_headers"] = {
                "anthropic-beta": "interleaved-thinking-2025-05-14"
            }
        llm = ChatAnthropic(**kwargs)
        if thinking is not None:
            llm = llm.bind(thinking=thinking)
        return llm

    def build_preamble(
        self,
        *,
        prompt: str,
    ) -> list[BaseMessage]:
        return [SystemMessage(content=[
            {
                "type": "text",
                "text": prompt,
                "cache_control": {"type": "ephemeral", "ttl": "1h"},
            },
        ])]

    def prepare_tools(self, tools: list) -> tuple[list, list]:
        llm_tools: list = []
        node_tools: list = []
        for tool in tools:
            if isinstance(tool, dict):
                if tool.get("type") == "web_search":
                    llm_tools.append(anthropic_web_search_tool)
                else:
                    llm_tools.append(tool)
                continue
            name = getattr(tool, "name", None)
            if name == "read_pdf":
                llm_tools.append(anthropic_read_pdf_tool)
                node_tools.append(anthropic_read_pdf_tool)
                continue
            if name == "read_image":
                llm_tools.append(anthropic_read_image_tool)
                node_tools.append(anthropic_read_image_tool)
                continue
            llm_tools.append(tool)
            node_tools.append(tool)
        # Add cache_control to last non-builtin tool for prompt caching.
        if llm_tools:
            for i in range(len(llm_tools) - 1, -1, -1):
                tool = llm_tools[i]
                if isinstance(tool, dict) and tool.get("type") in (
                    "web_search",
                    "web_search_20250305",
                ):
                    continue  # Skip builtin tools
                if not isinstance(tool, dict):
                    from langchain_anthropic import convert_to_anthropic_tool

                    tool = convert_to_anthropic_tool(tool)
                    llm_tools[i] = tool
                tool["cache_control"] = {"type": "ephemeral", "ttl": "1h"}
                break
        return llm_tools, node_tools

    def bind_reasoning(self, llm: Any, *, reasoning_effort: str, adaptive: bool = True) -> Any:
        model_name = _get_model_name(llm)
        if _supports_adaptive_thinking(model_name):
            effort_level = _map_effort_for_adaptive(reasoning_effort)
            if effort_level is None:
                return _strip_thinking(llm)
            # Always re-bind both thinking and output_config together.
            # bind_tools() on a RunnableBinding silently drops prior .bind()
            # kwargs, so the thinking param from create_chat_model may be lost.
            if not adaptive:
                # Force thinking on every call by using effort "max".
                # "max" is Opus 4.6 only and guarantees Claude always
                # thinks with no constraints on thinking depth.
                effort_level = "max"
            return llm.bind(
                thinking={"type": "adaptive"},
                output_config={"effort": effort_level},
            )
        # Older models: override thinking via .bind() (works because
        # create_chat_model leaves self.thinking=None on the constructor).
        inner = _get_inner_llm(llm)
        max_tokens = getattr(
            inner, "max_tokens", ANTHROPIC_DEFAULT_MAX_OUTPUT_TOKENS
        )
        thinking = _thinking_for_effort(reasoning_effort, max_tokens)
        if thinking is None:
            return _strip_thinking(llm)
        if not hasattr(llm, "bind"):
            return llm
        return llm.bind(thinking=thinking)

    def bind_reasoning_trace(self, llm: Any) -> Any:
        return llm

    @staticmethod
    def _add_conversation_cache_breakpoint(
        messages: list[BaseMessage],
    ) -> list[BaseMessage]:
        """Add a cache breakpoint on the last cacheable conversation message.

        This enables incremental conversation caching: on each LLM call
        the overlapping prefix of messages hits the Anthropic prompt cache,
        so only newly appended messages are processed as fresh input.

        Skipped message types:
        - SystemMessage: already cached via build_preamble.
        - ToolMessage: cache_control would land inside nested
          tool_result content, not on the tool_result block itself.
        - Messages whose last content block is a thinking block
          (thinking blocks cannot be cached per Anthropic API).
        - Messages with empty content (not cacheable).
        """
        if not messages:
            return messages

        from langchain_core.messages import ToolMessage

        for i in range(len(messages) - 1, -1, -1):
            msg = messages[i]
            if isinstance(msg, (SystemMessage, ToolMessage)):
                continue

            content = msg.content
            if not content:
                continue

            cache_marker = {"type": "ephemeral", "ttl": "1h"}

            if isinstance(content, str):
                new_content = [
                    {"type": "text", "text": content, "cache_control": cache_marker}
                ]
            elif isinstance(content, list):
                last_block = content[-1]
                # Thinking blocks cannot be cached directly.
                if isinstance(last_block, dict) and last_block.get("type") == "thinking":
                    continue
                new_content = list(content)
                if isinstance(last_block, dict):
                    last_block = {**last_block, "cache_control": cache_marker}
                else:
                    last_block = {
                        "type": "text",
                        "text": str(last_block),
                        "cache_control": cache_marker,
                    }
                new_content[-1] = last_block
            else:
                continue

            # Shallow-copy the list and replace only the target message.
            messages = list(messages)
            messages[i] = msg.model_copy(update={"content": new_content})
            break

        return messages

    def invoke(
        self,
        llm: Any,
        messages: list[BaseMessage],
        *,
        reasoning_effort: str | None = None,
    ) -> Any:
        messages = self._add_conversation_cache_breakpoint(messages)
        return llm.invoke(messages)

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
        # Check if thinking is active (via .bind() kwargs or constructor).
        has_thinking = (
            _has_thinking_in_bind_kwargs(llm)
            or getattr(_get_inner_llm(llm), "thinking", None) is not None
        )

        if has_thinking:
            # Thinking + structured output: Anthropic doesn't support forced
            # tool_choice with thinking, so we bind tools without it and
            # validate that the model actually called the tool.
            # This mirrors ChatAnthropic._get_llm_for_structured_output_when_thinking_is_enabled.
            return self._structured_output_with_thinking(
                llm, schema, include_raw=include_raw, strict=strict,
                tools=tools, reasoning_effort=reasoning_effort,
            )

        # No thinking — strip and use the standard path.
        llm = _strip_thinking(llm)
        kwargs: dict[str, Any] = {"include_raw": include_raw}
        if strict is not None:
            kwargs["strict"] = strict
        if tools is not None:
            kwargs["tools"] = tools
        return llm.with_structured_output(schema, **kwargs)

    def _structured_output_with_thinking(
        self,
        llm: Any,
        schema: Any,
        *,
        include_raw: bool,
        strict: bool | None = None,
        tools: list | None = None,
        reasoning_effort: str | None = None,
    ) -> Any:
        """Build a structured-output pipeline that preserves thinking blocks.

        Since forced tool_choice is incompatible with Anthropic thinking mode,
        we bind tools without tool_choice and validate the model called the tool.
        """
        from operator import itemgetter

        from langchain_core.exceptions import OutputParserException
        from langchain_core.output_parsers.openai_tools import PydanticToolsParser
        from langchain_core.runnables import RunnableMap, RunnablePassthrough
        from pydantic import BaseModel

        # Bind tools without tool_choice so thinking remains enabled.
        # Additional research tools are included alongside the schema tool
        # so the model can call research tools OR the structured-output tool.
        bind_kwargs: dict[str, Any] = {}
        if strict is not None:
            bind_kwargs["strict"] = strict
        all_tools = [schema] + list(tools or [])
        llm_with_tools = llm.bind_tools(all_tools, **bind_kwargs)
        # bind_tools() via __getattr__ drops .bind() kwargs (including
        # thinking). Re-apply thinking so the API request includes it.
        if reasoning_effort:
            llm_with_tools = self.bind_reasoning(
                llm_with_tools, reasoning_effort=reasoning_effort,
            )
        else:
            # Fallback: re-bind thinking from the original LLM's kwargs chain
            current = llm
            while hasattr(current, "kwargs"):
                th = current.kwargs.get("thinking")
                if th is not None:
                    llm_with_tools = llm_with_tools.bind(thinking=th)
                    break
                if not hasattr(current, "bound"):
                    break
                current = current.bound

        # Validate that the model produced a tool call.
        def _validate_tool_call(message: Any) -> Any:
            if not getattr(message, "tool_calls", None):
                raise OutputParserException(
                    "Model did not generate a tool call for structured output. "
                    "This can happen when thinking is enabled."
                )
            return message

        # Build the output parser for the schema.
        if isinstance(schema, type) and issubclass(schema, BaseModel):
            output_parser = PydanticToolsParser(
                tools=[schema], first_tool_only=True,
            )
        else:
            from langchain_core.output_parsers.openai_tools import (
                JsonOutputKeyToolsParser,
            )
            from langchain_anthropic import convert_to_anthropic_tool

            tool_name = convert_to_anthropic_tool(schema)["name"]
            output_parser = JsonOutputKeyToolsParser(
                key_name=tool_name, first_tool_only=True,
            )

        if include_raw:
            parser_assign = RunnablePassthrough.assign(
                parsed=itemgetter("raw") | output_parser,
                parsing_error=lambda _: None,
            )
            parser_none = RunnablePassthrough.assign(parsed=lambda _: None)
            parser_with_fallback = parser_assign.with_fallbacks(
                [parser_none], exception_key="parsing_error",
            )
            return (
                RunnableMap(raw=llm_with_tools | _validate_tool_call)
                | parser_with_fallback
            )
        return llm_with_tools | _validate_tool_call | output_parser
