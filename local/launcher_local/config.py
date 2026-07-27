"""Reading ``local/config.env`` — the local launcher's own configuration.

Deliberately separate from ``launcher.settings``: that module's job is to
*remove* endpoint and credential variables, and this one's job is to supply
them. Keeping them apart is what makes the main launcher's guarantee readable
in one place.

The variables are named ``LOCAL_MODEL_*`` rather than ``ANTHROPIC_*`` on
purpose. The main launcher scrubs anything called ``ANTHROPIC_*`` out of the
ambient environment, so naming them that way here would make the two paths
interfere: exporting ``ANTHROPIC_BASE_URL`` in your shell must keep doing
nothing to a normal ``./madrun.sh`` run. The rename to ``ANTHROPIC_*`` happens
once, at the moment of exec, and only for a run started through this launcher.
"""
from __future__ import annotations

import os
from pathlib import Path

LOCAL_DIR = Path(__file__).resolve().parents[1]
CONFIG_ENV = LOCAL_DIR / "config.env"

BASE_URL_VAR = "LOCAL_MODEL_BASE_URL"
TOKEN_VAR = "LOCAL_MODEL_TOKEN"
MODEL_VAR = "LOCAL_MODEL_NAME"
EFFORT_VAR = "LOCAL_MODEL_EFFORT"


def load_local_config(path: Path | None = None) -> None:
    """Populate ``os.environ`` from ``local/config.env`` without overriding it.

    Same precedence rule as the main launcher: caller env > config.env >
    defaults, achieved with ``setdefault`` because the caller's environment is
    already in ``os.environ`` by the time this runs.
    """
    path = path or CONFIG_ENV
    if not path.is_file():
        return
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        os.environ.setdefault(key, value)


def endpoint_env() -> dict[str, str]:
    """The container environment that points Claude Code at your endpoint.

    Returns ``{}`` when no base URL is configured, so the caller can refuse to
    start rather than silently falling back to Anthropic — a local run that
    quietly used the hosted API would be a surprising and possibly expensive
    outcome.

    A base URL with no token is valid: an endpoint on a trusted network may not
    authenticate at all. A token with no base URL is not, and yields ``{}``.
    """
    base_url = os.environ.get(BASE_URL_VAR, "").strip()
    if not base_url:
        return {}
    env = {"ANTHROPIC_BASE_URL": base_url}
    token = os.environ.get(TOKEN_VAR, "").strip()
    if token:
        env["ANTHROPIC_AUTH_TOKEN"] = token
    return env


def model_args() -> list[str]:
    """``--model`` / ``--effort`` for the configured local model, if any.

    Appended before the user's own arguments so an explicit ``--model`` on the
    command line still wins.
    """
    args: list[str] = []
    model = os.environ.get(MODEL_VAR, "").strip()
    if model:
        args += ["--model", model]
    effort = os.environ.get(EFFORT_VAR, "").strip()
    if effort:
        args += ["--effort", effort]
    return args


def redacted_summary() -> str:
    """One line describing the endpoint, with the token never printed."""
    base_url = os.environ.get(BASE_URL_VAR, "").strip()
    model = os.environ.get(MODEL_VAR, "").strip() or "(claude's default)"
    auth = "with token" if os.environ.get(TOKEN_VAR, "").strip() else "no token"
    return f"{base_url}  [model: {model}, {auth}]"
