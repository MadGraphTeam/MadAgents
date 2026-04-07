"""Content-addressed LLM response cache.

Stores LLM responses keyed by a SHA-256 hash of the prompt and parameters.
Activated per-run via set_llm_cache_dir().  Thread-safe (atomic writes
via tempfile + rename, guarded by a threading.Lock).
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import threading
from pathlib import Path


_llm_cache_dir: Path | None = None
_llm_cache_lock = threading.Lock()


def set_llm_cache_dir(path: Path) -> None:
    """Activate the LLM response cache for this process.

    Called once at the start of each pipeline phase with the run-level
    cache directory (e.g. ``run_dir / "cache" / "llm"``).
    """
    global _llm_cache_dir
    path.mkdir(parents=True, exist_ok=True)
    _llm_cache_dir = path


def get_llm_cache_dir() -> Path | None:
    """Return the currently active cache directory, or None."""
    return _llm_cache_dir


def cache_key(*parts: str) -> str:
    """Compute a SHA-256 cache key from one or more string parts."""
    h = hashlib.sha256()
    for part in parts:
        h.update(part.encode("utf-8"))
        h.update(b"\x00")  # separator
    return h.hexdigest()


def cache_get(key: str) -> dict | None:
    """Return cached value for *key*, or None on miss."""
    if _llm_cache_dir is None:
        return None
    path = _llm_cache_dir / f"{key}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def cache_put(key: str, value: dict) -> None:
    """Store *value* under *key*.  Atomic write (tmp + rename)."""
    if _llm_cache_dir is None:
        return
    path = _llm_cache_dir / f"{key}.json"
    tmp = None
    with _llm_cache_lock:
        try:
            fd, tmp = tempfile.mkstemp(
                dir=str(_llm_cache_dir), suffix=".tmp"
            )
            with os.fdopen(fd, "w") as f:
                json.dump(value, f)
            os.replace(tmp, str(path))
            tmp = None
        except Exception:
            if tmp:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass
