from __future__ import annotations

import os
from pathlib import Path

from .paths import REPO_ROOT

API_KEY_VARS: tuple[str, ...] = (
    # Direct LLM auth
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "LLM_API_KEY",
    # Endpoint redirection (could route auth elsewhere)
    "ANTHROPIC_API_URL",
    "ANTHROPIC_BASE_URL",
    "ANTHROPIC_CUSTOM_HEADERS",
    # Alternate auth backends — would change Claude Code's auth path
    "CLAUDE_CODE_USE_BEDROCK",
    "CLAUDE_CODE_USE_VERTEX",
    "ANTHROPIC_BEDROCK_BASE_URL",
    "AWS_BEARER_TOKEN_BEDROCK",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "ANTHROPIC_VERTEX_PROJECT_ID",
    # The same three classes again for Codex. A codex run authenticates the way
    # a claude run does — through the config directory the launcher binds — so
    # an ambient key or redirected endpoint is no more welcome here than there.
    "CODEX_API_KEY",
    "CODEX_ACCESS_TOKEN",
    "OPENAI_BASE_URL",
)

API_KEY_SUFFIXES: tuple[str, ...] = ("_API_KEY", "_AUTH_TOKEN")


def load_config_env(path: Path | None = None) -> None:
    """Parse config.env and populate os.environ without overriding caller env.

    Caller-env-wins precedence is achieved by os.environ.setdefault, so this
    must run after the caller env is already in os.environ (which it always
    is, since Python inherits it at startup).
    """
    path = path or (REPO_ROOT / "config.env")
    if not path.is_file():
        return
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if not key:
            continue
        value = value.strip()
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        os.environ.setdefault(key, value)


def scrub_api_keys(extra: tuple[str, ...] = ()) -> None:
    """Remove API-key / alt-auth env vars so they don't leak into subprocesses.

    Scrubs three categories:
    1. Explicit names in ``API_KEY_VARS`` (and any extras passed in).
    2. Anything whose name ends with a suffix in ``API_KEY_SUFFIXES``
       (catches custom ``FOO_API_KEY`` / ``FOO_AUTH_TOKEN`` vars).

    Must run before any ``subprocess.Popen`` / ``subprocess.run`` / apptainer
    exec so children (including MCP servers and spawned ``claude``) inherit
    a clean env.
    """
    for key in API_KEY_VARS + extra:
        os.environ.pop(key, None)
    for key in list(os.environ):
        if any(key.endswith(suf) for suf in API_KEY_SUFFIXES):
            os.environ.pop(key, None)


def assert_no_api_keys() -> None:
    """Raise ``RuntimeError`` if any auth-affecting env var is still set.

    Belt-and-suspenders check called immediately before the claude exec.
    Catches programming errors (e.g. an explicit ``--env`` re-introducing one).
    """
    leaked: list[str] = []
    for key in API_KEY_VARS:
        if key in os.environ:
            leaked.append(key)
    for key in os.environ:
        if any(key.endswith(suf) for suf in API_KEY_SUFFIXES) and key not in leaked:
            leaked.append(key)
    if leaked:
        raise RuntimeError(
            "API-key / alt-auth env vars present right before claude exec: "
            + ", ".join(sorted(leaked))
        )
