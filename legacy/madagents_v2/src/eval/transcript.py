"""Transcript capture for eval sessions.

Converts CLI stream-json events (already dicts) and writes them as
newline-delimited JSON (JSONL) trace files.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def message_to_dict(message: object) -> dict[str, Any]:
    """Convert a message to a JSON-serialisable dict.

    With the CLI stream-json backend, messages are already dicts.
    This function is kept for backward compatibility.
    """
    if isinstance(message, dict):
        return message
    # Fallback for unknown types.
    return {"type": type(message).__name__, "data": str(message)}


def write_transcript(messages: list, path: Path) -> None:
    """Write messages as segmented JSON to *path*.

    Groups consecutive messages from the same session into segments::

        [
          {"agent": "answerer", "messages": [...]},
          {"agent": "grader",   "messages": [...]},
          ...
        ]

    Accepts either raw SDK message objects or pre-converted dicts
    (as stored by :attr:`_BaseSDKSession.transcript`).
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    # Convert any raw SDK objects to dicts.
    entries = [
        msg if isinstance(msg, dict) else message_to_dict(msg)
        for msg in messages
    ]

    # Group consecutive entries by session name.
    segments: list[dict[str, Any]] = []
    for entry in entries:
        session = entry.get("session", "")
        # Copy without the session key for the segment payload.
        msg = {k: v for k, v in entry.items() if k != "session"}
        if segments and segments[-1]["agent"] == session:
            segments[-1]["messages"].append(msg)
        else:
            segments.append({"agent": session, "messages": [msg]})

    path.write_text(json.dumps(segments, indent=2))


def _indent(text: str, prefix: str = "│ ") -> str:
    """Indent every line of *text* with *prefix*."""
    return "\n".join(prefix + line for line in text.splitlines())


def _clean_message(entry: dict[str, Any]) -> dict[str, Any] | None:
    """Strip metadata from a transcript entry, keeping only workflow content.

    Returns ``None`` for events that should be dropped entirely
    (system/init, rate_limit_event, etc.).
    """
    t = entry.get("type", "")

    # Drop entirely.
    if t == "rate_limit_event":
        return None
    if t == "system" and entry.get("subtype") == "init":
        return None

    # Our recorded user prompt — keep as-is.
    if t == "user" and "prompt" in entry:
        return {"type": "user", "prompt": entry["prompt"]}

    # User messages (tool results) — keep tool_use_id, type, content.
    if t == "user" and "message" in entry:
        msg = entry["message"]
        content = msg.get("content", [])
        cleaned_content = []
        for block in content:
            if block.get("type") == "tool_result":
                cleaned = {
                    "type": "tool_result",
                    "tool_use_id": block.get("tool_use_id"),
                }
                # Keep content but strip internal metadata from it.
                if "content" in block:
                    cleaned["content"] = block["content"]
                cleaned_content.append(cleaned)
            else:
                cleaned_content.append(block)
        return {"type": "user", "message": {"role": "user", "content": cleaned_content}}

    # Assistant messages — keep text, tool_use, thinking text; strip metadata.
    if t == "assistant":
        msg = entry.get("message", {})
        content = msg.get("content", [])
        cleaned_content = []
        for block in content:
            bt = block.get("type", "")
            if bt == "text":
                text = block.get("text", "").strip()
                if text:
                    cleaned_content.append({"type": "text", "text": text})
            elif bt == "tool_use":
                cleaned = {"type": "tool_use", "id": block.get("id"), "name": block.get("name")}
                if "input" in block:
                    cleaned["input"] = block["input"]
                cleaned_content.append(cleaned)
            elif bt == "thinking":
                thinking = block.get("thinking", "").strip()
                if thinking:
                    cleaned_content.append({"type": "thinking", "thinking": thinking})
        if not cleaned_content:
            return None
        result: dict[str, Any] = {"type": "assistant", "content": cleaned_content}
        pid = entry.get("parent_tool_use_id")
        if pid:
            result["parent_tool_use_id"] = pid
        return result

    # System task events (subagent lifecycle) — keep.
    if t == "system" and entry.get("subtype") in ("task_started", "task_completed"):
        cleaned: dict[str, Any] = {"type": "system", "subtype": entry["subtype"]}
        for key in ("task_id", "tool_use_id", "description", "task_type", "prompt", "result"):
            if key in entry:
                cleaned[key] = entry[key]
        return cleaned

    # Result event — keep summary, drop usage details.
    if t == "result":
        cleaned = {"type": "result"}
        for key in ("result", "is_error", "session_id", "num_turns", "duration_ms", "cost_usd"):
            if key in entry:
                cleaned[key] = entry[key]
        return cleaned

    # Unknown event types — drop.
    return None


def write_workflow(messages: list, directory: Path) -> None:
    """Write per-session cleaned workflow transcripts to *directory*.

    Creates one JSON file per session under ``directory/``::

        directory/
          answerer.json
          supervisor.json
          ...

    Each file contains a flat list of cleaned events (tool calls,
    results, text, subagent activity) with metadata stripped.
    """
    directory.mkdir(parents=True, exist_ok=True)

    entries = [
        msg if isinstance(msg, dict) else message_to_dict(msg)
        for msg in messages
    ]

    # Group by session name.
    sessions: dict[str, list[dict[str, Any]]] = {}
    for entry in entries:
        session = entry.get("session", "") or "default"
        cleaned = _clean_message(entry)
        if cleaned is not None:
            sessions.setdefault(session, []).append(cleaned)

    for session_name, events in sessions.items():
        filename = f"{session_name}.json"
        (directory / filename).write_text(json.dumps(events, indent=2))


def write_summary(messages: list, path: Path) -> None:
    """Write a human-readable conversation summary to *path*.

    Shows only user prompts and assistant text responses, grouped
    by session.  Tool calls, tool results, system messages, and
    other internal SDK traffic are omitted.  Consecutive assistant
    messages within the same session are merged.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    entries = [
        msg if isinstance(msg, dict) else message_to_dict(msg)
        for msg in messages
    ]

    lines: list[str] = []
    current_session = None
    last_role = None  # "user" or "assistant" — for merging
    session_separator = "=" * 60
    msg_width = 56

    def _session_header(name: str) -> None:
        lines.append("")
        lines.append(session_separator)
        lines.append(f"  {name or '(unnamed)'}")
        lines.append(session_separator)

    def _msg_header(role: str) -> None:
        label = role.capitalize()
        lines.append("")
        lines.append(f"─── {label} " + "─" * (msg_width - len(label)))

    for entry in entries:
        session = entry.get("session", "")
        t = entry.get("type", "")

        # Our recorded user prompt.
        if t == "user" and "prompt" in entry:
            if session != current_session:
                current_session = session
                _session_header(session)
                last_role = None
            _msg_header("user")
            lines.append(_indent(entry["prompt"]))
            last_role = "user"

        # Assistant text (skip entries that only have tool calls).
        elif t == "assistant":
            content = entry.get("message", {}).get("content", [])
            text_parts = [
                b["text"] for b in content
                if b.get("type") == "text" and b.get("text", "").strip()
            ]
            if text_parts:
                if session != current_session:
                    current_session = session
                    _session_header(session)
                    last_role = None
                text = "\n".join(text_parts)
                if last_role == "assistant":
                    # Merge with previous assistant block.
                    lines.append(_indent(text))
                else:
                    _msg_header("assistant")
                    lines.append(_indent(text))
                last_role = "assistant"

        # Result — show cost/turns as a footer.
        elif t == "result":
            cost = entry.get("cost_usd")
            turns = entry.get("num_turns", 0)
            duration = entry.get("duration_ms", 0)
            usage = entry.get("usage", {})
            parts = [f"{turns} turns", f"{duration / 1000:.1f}s"]
            input_tok = usage.get("input_tokens") or usage.get("input", 0)
            output_tok = usage.get("output_tokens") or usage.get("output", 0)
            if input_tok or output_tok:
                parts.append(f"{input_tok + output_tok:,} tokens ({input_tok:,} in, {output_tok:,} out)")
            if cost:
                parts.append(f"~${cost:.4f}")

            lines.append("")
            lines.append(f"   [{', '.join(parts)}]")
            last_role = None

    path.write_text("\n".join(lines).strip() + "\n")
