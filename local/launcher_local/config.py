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
once, at the moment of exec, and only for a ``claude_code`` run started through
this launcher. An ``opencode`` run needs no rename at all — the same
``LOCAL_MODEL_*`` values are written into a generated config file instead, and
never enter the environment.
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
PROVIDER_VAR = "LOCAL_PROVIDER"

#: The provider id the generated opencode config declares, so a model is
#: addressed as ``local/<model>``. Fixed rather than configurable: it appears in
#: the generated config, in ``--model``, and in the notes, and a name that could
#: drift between them would be a debugging trap for no benefit.
OPENCODE_PROVIDER_ID = "local"
#: The AI SDK package opencode uses for an OpenAI-compatible endpoint. Bundled
#: into the binary as of 1.18.11 — declaring it costs nothing and keeps the
#: config honest about what it expects.
OPENCODE_NPM = "@ai-sdk/openai-compatible"


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


def local_provider() -> str:
    """Which CLI a local run uses by default. See setup.PROVIDERS_BY_BACKEND."""
    return os.environ.get(PROVIDER_VAR, "").strip() or "opencode"


def write_token_file(directory: Path) -> Path | None:
    """Write the bearer token to a ``0600`` file, or return None if there is none.

    The credential lands in the **run workdir** — ephemeral, under the already
    gitignored ``run_dir/`` — and deliberately *not* in the instance:
    ``setup._copy_system_tree`` copies an instance's whole tree on fork, so
    anything credential-shaped placed there would propagate into every fork and
    sit at whatever mode ``cp --preserve=mode`` carried.

    Created with the mode set at open() time rather than chmod()ed afterwards,
    so there is no window in which it exists world-readable.
    """
    token = os.environ.get(TOKEN_VAR, "").strip()
    if not token:
        return None
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "opencode-token"
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as fh:
        fh.write(token)
    return path


def opencode_overlay_config(container_token_path: str | None) -> dict:
    """The endpoint half of the opencode config, as a merge-in overlay.

    Kept out of the instance's own ``opencode.json`` on purpose. That file is
    the *agent system* — generated by ``tools/render_opencode.py``, tracked, and
    forked along with the instance. The endpoint is neither: it is a property of
    this launch, it can be overridden per run, and it names a host that has no
    business in git. opencode merges ``OPENCODE_CONFIG`` over the project config,
    which is exactly the seam for that split.

    The API key is a ``{file:}`` **reference**, never the value, so the secret
    exists in one place on disk (mode 0600, in the run workdir) and reaches the
    model without ever becoming an environment variable — which is what lets the
    opencode path keep ``assert_no_api_keys()`` switched on.
    """
    base_url = os.environ.get(BASE_URL_VAR, "").strip()
    model = os.environ.get(MODEL_VAR, "").strip()
    options: dict[str, str] = {"baseURL": base_url}
    if container_token_path:
        options["apiKey"] = f"{{file:{container_token_path}}}"
    config: dict = {
        "$schema": "https://opencode.ai/config.json",
        "provider": {
            OPENCODE_PROVIDER_ID: {
                "npm": OPENCODE_NPM,
                "name": "Self-hosted (local/config.env)",
                "options": options,
                "models": {model: {"name": model}} if model else {},
            },
        },
    }
    if model:
        # Saves the operator selecting it in the TUI every session. An explicit
        # --model on the command line still wins, as it does on the other path.
        config["model"] = f"{OPENCODE_PROVIDER_ID}/{model}"
    return config


def redacted_summary() -> str:
    """One line describing the endpoint, with the token never printed."""
    base_url = os.environ.get(BASE_URL_VAR, "").strip()
    model = os.environ.get(MODEL_VAR, "").strip() or "(the CLI's default)"
    auth = "with token" if os.environ.get(TOKEN_VAR, "").strip() else "no token"
    return f"{base_url}  [model: {model}, {auth}]"
