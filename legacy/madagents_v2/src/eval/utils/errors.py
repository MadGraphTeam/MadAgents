"""Transient error detection and reporting."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path


EX_TEMPFAIL = 75  # BSD sysexits convention: "try again later"


class TransientError(Exception):
    """Raised when a transient error (auth expiry, rate limit) is detected.

    All pipeline phases catch this to stop cleanly and allow resumption.
    """
    pass


# Patterns that indicate transient auth/rate-limit failures.
_TRANSIENT_PATTERNS = [
    re.compile(r"authentication_failed", re.IGNORECASE),
    re.compile(r"oauth\s+token\s+has\s+expired", re.IGNORECASE),
    re.compile(r"failed\s+to\s+authenticate", re.IGNORECASE),
    re.compile(r"token\s+has\s+expired", re.IGNORECASE),
    re.compile(r"rate_limit", re.IGNORECASE),
    re.compile(r"you've hit your limit", re.IGNORECASE),
    re.compile(r"you.ve hit your limit", re.IGNORECASE),
]

_RATE_LIMIT_PATTERNS = [
    re.compile(r"rate_limit", re.IGNORECASE),
    re.compile(r"you.ve hit your limit", re.IGNORECASE),
]
_AUTH_PATTERNS = [
    re.compile(r"authentication_failed", re.IGNORECASE),
    re.compile(r"oauth\s+token\s+has\s+expired", re.IGNORECASE),
    re.compile(r"failed\s+to\s+authenticate", re.IGNORECASE),
    re.compile(r"token\s+has\s+expired", re.IGNORECASE),
]


def detect_transient_error(text: str) -> str | None:
    """Check a string for known transient error patterns.

    Returns a short description of the matched pattern, or None.
    """
    if not text:
        return None
    for pat in _TRANSIENT_PATTERNS:
        m = pat.search(text)
        if m:
            return m.group(0)
    return None


def check_trace_for_transient_error(trace_path: Path) -> str | None:
    """Scan a stream-JSON trace file for transient errors.

    Reads from the end of the file (errors tend to appear last).
    """
    if not trace_path.exists():
        return None
    try:
        lines = trace_path.read_text().splitlines()
    except OSError:
        return None

    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        if event.get("type") == "result" and event.get("is_error"):
            result_text = event.get("result", "")
            match = detect_transient_error(result_text)
            if match:
                return match

        if event.get("type") == "assistant":
            error_field = event.get("error", "")
            if error_field:
                match = detect_transient_error(str(error_field))
                if match:
                    return match

        error_field = event.get("error", "")
        if error_field:
            match = detect_transient_error(str(error_field))
            if match:
                return match

    return None


def find_transient_error_details(run_dir: Path) -> dict:
    """Scan trace files in a run directory for transient error details.

    Returns a dict with:
        resets_at: int|None -- max resetsAt Unix timestamp across all traces
        error_messages: list[str] -- human-readable error messages
        error_type: str -- "rate_limit", "auth", or "unknown"
    """
    resets_at = None
    error_messages: list[str] = []
    error_type = "unknown"

    trace_files = sorted(run_dir.glob("questions/*/trace*.jsonl"))

    for trace_path in trace_files:
        try:
            lines = trace_path.read_text().splitlines()
        except OSError:
            continue

        for line in lines[:5]:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("type") == "rate_limit_event":
                info = event.get("rate_limit_info", {})
                ts = info.get("resetsAt")
                if isinstance(ts, (int, float)) and ts > 0:
                    if resets_at is None or ts > resets_at:
                        resets_at = int(ts)

        for line in lines[-20:]:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            msg = None
            if event.get("type") == "result" and event.get("is_error"):
                msg = event.get("result", "")
            elif event.get("type") == "assistant" and event.get("error"):
                msg = str(event["error"])
            elif event.get("error"):
                msg = str(event["error"])

            if msg and detect_transient_error(msg):
                if msg not in error_messages:
                    error_messages.append(msg)

    all_text = " ".join(error_messages)
    if any(p.search(all_text) for p in _RATE_LIMIT_PATTERNS):
        error_type = "rate_limit"
    elif any(p.search(all_text) for p in _AUTH_PATTERNS):
        error_type = "auth"

    return {
        "resets_at": resets_at,
        "error_messages": error_messages,
        "error_type": error_type,
    }


def write_transient_error_info(run_dir: Path, phase: str) -> None:
    """Write transient_error.json with details extracted from trace files.

    Non-fatal: silently ignores write failures so the exit 75 is not suppressed.
    """
    try:
        details = find_transient_error_details(run_dir)
        info = {
            "phase": phase,
            "error_type": details["error_type"],
            "error_messages": details["error_messages"],
            "resets_at": details["resets_at"],
            "detected_at": datetime.now(timezone.utc).isoformat(),
        }
        (run_dir / "transient_error.json").write_text(
            json.dumps(info, indent=2)
        )
    except Exception:
        pass
