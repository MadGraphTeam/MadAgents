from __future__ import annotations

import os
from typing import Any

from langchain_core.messages import BaseMessage, SystemMessage
from langchain_openai import ChatOpenAI

from madagents.llm.runtime import LLMRuntime


def _resolve_api_key(primary_env: str) -> str:
    primary = os.environ.get(primary_env, "").strip()
    if primary:
        return primary
    fallback = os.environ.get("LLM_API_KEY", "").strip()
    return fallback


class OpenAILLMRuntime(LLMRuntime):
    """OpenAI runtime implementation preserving existing call behavior."""

    def create_chat_model(
        self,
        *,
        model: str,
        reasoning_effort: str,
        verbosity: str | None,
        max_tokens: int,
    ) -> ChatOpenAI:
        kwargs: dict[str, Any] = {
            "model": model,
            "base_url": None,
            "api_key": _resolve_api_key("OPENAI_API_KEY"),
            "use_responses_api": True,
            "reasoning": {"effort": reasoning_effort},
            "max_tokens": max_tokens,
        }
        if verbosity is not None:
            kwargs["verbosity"] = verbosity
        return ChatOpenAI(**kwargs)

    def build_preamble(
        self,
        *,
        prompt: str,
    ) -> list[BaseMessage]:
        return [
            SystemMessage(
                content=prompt,
                additional_kwargs={"__openai_role__": "developer"},
            ),
        ]

    def prepare_tools(self, tools: list) -> tuple[list, list]:
        llm_tools = list(tools)
        node_tools = [tool for tool in tools if not isinstance(tool, dict)]
        return llm_tools, node_tools

    def bind_reasoning(self, llm: Any, *, reasoning_effort: str, adaptive: bool = True) -> Any:
        return llm.bind(reasoning={"effort": reasoning_effort})

    def bind_reasoning_trace(self, llm: Any) -> Any:
        return llm.bind(include=["reasoning.encrypted_content"])

    def invoke(
        self,
        llm: Any,
        messages: list[BaseMessage],
        *,
        reasoning_effort: str | None = None,
    ) -> Any:
        if isinstance(reasoning_effort, str) and reasoning_effort:
            return llm.invoke(messages, reasoning={"effort": reasoning_effort})
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
        if tools is not None:
            return self._structured_output_with_tools(
                llm, schema, tools=tools, include_raw=include_raw, strict=strict,
                include_reasoning_trace=include_reasoning_trace,
                reasoning_effort=reasoning_effort,
            )
        kwargs: dict[str, Any] = {"include_raw": include_raw}
        if strict is not None:
            kwargs["strict"] = strict
        if include_reasoning_trace:
            kwargs["include"] = ["reasoning.encrypted_content"]
        if isinstance(reasoning_effort, str) and reasoning_effort:
            kwargs["reasoning"] = {"effort": reasoning_effort}
        return llm.with_structured_output(schema, **kwargs)

    def _structured_output_with_tools(
        self,
        llm: Any,
        schema: Any,
        *,
        tools: list,
        include_raw: bool,
        strict: bool | None = None,
        include_reasoning_trace: bool = False,
        reasoning_effort: str | None = None,
    ) -> Any:
        """Structured output + tool calling via json_schema response_format + bind_tools.

        The model either calls research tools (parsed=None) or produces
        structured JSON text following the schema (parsed=<schema>).

        The Pydantic class is passed directly as response_format so that
        langchain/OpenAI SDK handle strict-mode schema conversion (adding
        additionalProperties, marking all fields required, etc.).
        """
        from langchain_core.runnables import RunnableLambda

        # 1. Bind research tools
        llm_with_tools = llm.bind_tools(tools)

        # 2. Bind response_format (pass Pydantic class directly — langchain
        #    converts it to text_format for the Responses API, which the
        #    SDK translates into a strict-compliant json_schema constraint).
        bind_kwargs: dict[str, Any] = {"response_format": schema}
        if include_reasoning_trace:
            bind_kwargs["include"] = ["reasoning.encrypted_content"]
        if isinstance(reasoning_effort, str) and reasoning_effort:
            bind_kwargs["reasoning"] = {"effort": reasoning_effort}
        llm_final = llm_with_tools.bind(**bind_kwargs)

        # 3. Build parser: tool_calls → research turn (parsed=None);
        #    text content → parse as schema
        def _extract_text_content(content):
            """Extract text string from content (may be str or list of blocks)."""
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        return block.get("text", "")
                return ""
            return str(content)

        def _parse_response(message):
            if getattr(message, "tool_calls", None):
                return {"raw": message, "parsed": None, "parsing_error": None}
            try:
                text = _extract_text_content(message.content)
                parsed = schema.model_validate_json(text)
                return {"raw": message, "parsed": parsed, "parsing_error": None}
            except Exception as e:
                return {"raw": message, "parsed": None, "parsing_error": e}

        if include_raw:
            return llm_final | RunnableLambda(_parse_response)
        else:
            def _parse_only(message):
                if getattr(message, "tool_calls", None):
                    return None
                text = _extract_text_content(message.content)
                return schema.model_validate_json(text)
            return llm_final | RunnableLambda(_parse_only)
