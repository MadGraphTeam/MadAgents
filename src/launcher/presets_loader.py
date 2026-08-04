"""Agent-system configuration.

The configuration describes *what* is run — the ``.claude/`` tree, the model,
CLI limits, and (optionally) a system-prompt file to append.

An agent system is a directory shaped like this::

    <dir>/
    ├── config.yaml     (required)
    └── .claude/        (required iff claude_dir_path is omitted)

``config.yaml`` may set ``claude_dir_path`` to a repo-relative directory whose
``.claude/`` tree should be copied into a run instance. If omitted,
``<dir>/.claude/`` is used. In both cases symlinks are dereferenced while
copying, so the resulting tree is self-contained.

The shipped system is ``madagents/``; a run instance built by
``src/launcher/setup.py`` has the same shape, which is what makes an instance
re-runnable and forkable.

``provider:`` selects the CLI the system is written for. ``claude_code`` (the
default) is the shape above. ``codex`` is the same system rendered for the
Codex CLI by ``tools/render_codex.py``, and carries two trees instead of one —
the roster at ``.codex/`` and the skills at ``.agents/``, which is where Codex
looks for each::

    <dir>/
    ├── config.yaml           provider: codex
    ├── .codex/agents/*.toml  the roster (card + slate per role)
    ├── .codex/config.toml    agent cap, permission profile
    ├── .agents/skills/       the workflows
    └── prompts/              the lead's append

Both shapes are consumed by the same harness; :meth:`Preset.agent_dirs` is what
lets the launcher bind either without knowing which it has.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .paths import REPO_ROOT


VALID_BIND_MODES = {"ro", "rw"}

CLAUDE_CODE = "claude_code"
CODEX = "codex"
OPENCODE = "opencode"
VALID_PROVIDERS = {CLAUDE_CODE, CODEX, OPENCODE}

# Keys accepted in config.yaml. ``description``, ``model`` and
# ``reasoning_effort`` are accepted but unused — they carry no runtime meaning,
# so they are tolerated (older configs set them) and ignored rather than
# rejected as unexpected keys. A run instance keeps a verbatim copy of the
# config it was built from (see setup.py:_materialize_yaml), so dropping these
# from the set would make every pre-existing instance unloadable.
#
# ``model`` / ``reasoning_effort`` stopped being honoured because a madrun run
# is interactive: the operator picks the model, in-session or on the command
# line. Do not re-add them here — see the note beside the argv passthrough in
# code.py.
_ALLOWED_KEYS = {
    "name", "description", "provider", "claude_dir_path", "mount_madgraph_docs",
    "madgraph_docs_path",
    "model", "reasoning_effort", "max_turns", "disallowed_tools",
    "append_system_prompt_file",
    "extra_binds",
    "auto_memory_enabled",
}


@dataclass(frozen=True)
class ExtraBind:
    """A general-purpose host→container bind-mount declared by a preset.

    ``host`` is an absolute filesystem path (resolved at preset-load time
    from the YAML's repo-relative or absolute string). ``container`` is an
    absolute in-container path. ``mode`` is ``"ro"`` or ``"rw"``.
    """
    host: Path
    container: str
    mode: str  # "ro" or "rw"


@dataclass
class Preset:
    """A benchmark preset — what we're testing."""

    name: str
    mount_madgraph_docs: bool
    preset_dir: Path                                      # directory containing config.yaml
    claude_dir: Path | None                               # source .claude/ (claude_code only)
    provider: str = CLAUDE_CODE                           # which CLI this system is written for
    madgraph_docs_path: str | None = None                 # repo-relative override; falls back to MADGRAPH_DOCS env
    max_turns: int | None = None
    disallowed_tools: list[str] = field(default_factory=list)
    append_system_prompt_file: str | list[str] | None = None
    extra_binds: list[ExtraBind] = field(default_factory=list)  # additional host→container mounts
    auto_memory_enabled: bool = False  # the system carries a learned tier (see setup.py)

    @property
    def is_codex(self) -> bool:
        return self.provider == CODEX

    @property
    def is_opencode(self) -> bool:
        return self.provider == OPENCODE

    def agent_dirs(self) -> list[tuple[Path, str]]:
        """(host dir, in-container path) for the trees that carry the system.

        Claude Code keeps everything under one ``.claude/``; Codex splits the
        roster and the skills across two directories it discovers by name. The
        launcher binds whatever this returns, so it never has to branch on the
        provider to build its mount list — the container layout mirrors the
        instance layout either way, which is what keeps a path written in a card
        (``.madagents/wiki/...``) true in both.
        """
        if self.is_codex:
            return [
                (self.preset_dir / ".codex", "/output/.codex"),
                (self.preset_dir / ".agents", "/output/.agents"),
            ]
        if self.is_opencode:
            # Three, and every one of them load-bearing:
            #   .opencode/  the config + the card bodies its prompts point at
            #   .claude/    the skills (opencode reads that tree natively) and
            #               the learned tier, at the very paths Claude Code uses
            #   prompts/    the lead's discipline, which `instructions` resolves
            #               from the PROJECT ROOT — not from the config's dir
            # The last one is why prompts/ is bound at all: on Claude Code the
            # launcher reads that file host-side and passes it as an append, so
            # it never needs to exist in the container.
            return [
                (self.preset_dir / ".opencode", "/output/.opencode"),
                (self.preset_dir / ".claude", "/output/.claude"),
                (self.preset_dir / "prompts", "/output/prompts"),
            ]
        assert self.claude_dir is not None  # enforced by load_preset
        return [(self.claude_dir, "/output/.claude")]

    def resolve_system_prompt(self, repo_root: Path) -> str:
        """Read and concatenate the configured system-prompt-append files.

        ``append_system_prompt_file`` may be a single path or a list of paths.
        Relative paths are resolved against *repo_root*. Files are joined with
        a blank line between them so each appended block stands alone.
        """
        if not self.append_system_prompt_file:
            return ""
        paths = self.append_system_prompt_file
        if isinstance(paths, str):
            paths = [paths]
        chunks: list[str] = []
        for path_str in paths:
            p = Path(path_str)
            if not p.is_absolute():
                p = repo_root / p
            chunks.append(p.read_text())
        return "\n\n".join(chunks)


def _repo_root() -> Path:
    return REPO_ROOT


def _parse_extra_binds(raw: object, yaml_path: Path) -> list[ExtraBind]:
    """Validate and resolve ``extra_binds`` entries from config.yaml.

    Each entry is a mapping with required keys ``host``, ``container``, ``mode``.
    ``host`` may be repo-relative or absolute; resolved to an absolute Path here.
    ``container`` must be an absolute in-container path.
    ``mode`` must be one of ``VALID_BIND_MODES`` (``ro`` or ``rw``).
    For ``mode: rw`` entries the host directory is created on demand if missing
    so the first run does not need a manual ``mkdir`` and the bind succeeds.
    Returns an empty list when ``raw`` is None or an empty list.
    """
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ValueError(
            f"{yaml_path}: extra_binds must be a list of mappings, "
            f"got {type(raw).__name__}"
        )
    out: list[ExtraBind] = []
    repo_root = _repo_root()
    for i, entry in enumerate(raw):
        if not isinstance(entry, dict):
            raise ValueError(
                f"{yaml_path}: extra_binds[{i}] must be a mapping, "
                f"got {type(entry).__name__}"
            )
        required = {"host", "container", "mode"}
        missing = required - entry.keys()
        if missing:
            raise ValueError(
                f"{yaml_path}: extra_binds[{i}] missing keys: {sorted(missing)}"
            )
        unknown = entry.keys() - required
        if unknown:
            raise ValueError(
                f"{yaml_path}: extra_binds[{i}] unexpected keys: {sorted(unknown)}"
            )
        host_raw = entry["host"]
        container = entry["container"]
        mode = entry["mode"]
        if not isinstance(host_raw, str) or not host_raw:
            raise ValueError(f"{yaml_path}: extra_binds[{i}].host must be a non-empty string")
        if not isinstance(container, str) or not container.startswith("/"):
            raise ValueError(
                f"{yaml_path}: extra_binds[{i}].container must be an absolute "
                f"in-container path (start with '/'), got {container!r}"
            )
        if mode not in VALID_BIND_MODES:
            raise ValueError(
                f"{yaml_path}: extra_binds[{i}].mode must be one of "
                f"{sorted(VALID_BIND_MODES)}, got {mode!r}"
            )
        host_path = Path(host_raw)
        if not host_path.is_absolute():
            host_path = repo_root / host_path
        host_path = host_path.resolve()
        if mode == "rw":
            host_path.mkdir(parents=True, exist_ok=True)
        elif not host_path.exists():
            raise ValueError(
                f"{yaml_path}: extra_binds[{i}].host {host_path} does not exist "
                f"(mode=ro requires the path to already exist)"
            )
        out.append(ExtraBind(host=host_path, container=container, mode=mode))
    return out


def load_preset(preset_dir: Path) -> Preset:
    """Load an agent system from ``<dir>/config.yaml`` and validate it."""
    yaml_path = preset_dir / "config.yaml"
    if not yaml_path.is_file():
        raise FileNotFoundError(f"{preset_dir}: missing config.yaml")

    data = yaml.safe_load(yaml_path.read_text())
    if not isinstance(data, dict):
        raise ValueError(
            f"{yaml_path}: preset must be a YAML mapping, got {type(data).__name__}"
        )

    required = {"name", "mount_madgraph_docs"}
    missing = required - data.keys()
    if missing:
        raise ValueError(f"{yaml_path}: missing required keys: {sorted(missing)}")

    extra = data.keys() - _ALLOWED_KEYS
    if extra:
        raise ValueError(
            f"{yaml_path}: unexpected keys: {sorted(extra)}"
        )

    provider = data.get("provider", CLAUDE_CODE)
    if provider not in VALID_PROVIDERS:
        raise ValueError(
            f"{yaml_path}: provider must be one of {sorted(VALID_PROVIDERS)}, got {provider!r}"
        )

    claude_dir: Path | None = None
    if provider == CODEX:
        if data.get("claude_dir_path"):
            raise ValueError(
                f"{yaml_path}: claude_dir_path does not apply to provider: codex "
                f"(the system lives in .codex/ and .agents/)"
            )
        for required in (".codex/agents", ".agents/skills"):
            if not (preset_dir / required).is_dir():
                raise ValueError(
                    f"{yaml_path}: provider is codex but {preset_dir / required} is missing. "
                    f"Render the tree: python3 tools/render_codex.py"
                )
    elif provider == OPENCODE:
        if data.get("claude_dir_path"):
            raise ValueError(
                f"{yaml_path}: claude_dir_path does not apply to provider: opencode "
                f"(the system lives in .opencode/, .claude/ and prompts/)"
            )
        for required in (".opencode/cards", ".claude/skills", "prompts"):
            if not (preset_dir / required).is_dir():
                raise ValueError(
                    f"{yaml_path}: provider is opencode but {preset_dir / required} is missing. "
                    f"Render the tree: python3 tools/render_opencode.py"
                )
        if not (preset_dir / ".opencode" / "opencode.json").is_file():
            raise ValueError(
                f"{yaml_path}: provider is opencode but "
                f"{preset_dir / '.opencode' / 'opencode.json'} is missing — that file IS the "
                f"roster. Render the tree: python3 tools/render_opencode.py"
            )
    else:
        claude_dir_path = data.get("claude_dir_path")
        if claude_dir_path is None:
            claude_dir = (preset_dir / ".claude").resolve()
        else:
            p = Path(claude_dir_path)
            claude_dir = p.resolve() if p.is_absolute() else (_repo_root() / p).resolve()
        if not claude_dir.is_dir():
            raise ValueError(
                f"{yaml_path}: claude_dir resolves to {claude_dir}, which is not a directory. "
                f"Either add a .claude/ subdirectory to the preset or fix claude_dir_path."
            )

    extra_binds = _parse_extra_binds(data.get("extra_binds"), yaml_path)

    preset = Preset(
        name=data["name"],
        mount_madgraph_docs=bool(data["mount_madgraph_docs"]),
        preset_dir=preset_dir,
        claude_dir=claude_dir,
        provider=provider,
        madgraph_docs_path=data.get("madgraph_docs_path"),
        max_turns=data.get("max_turns"),
        disallowed_tools=list(data.get("disallowed_tools", []) or []),
        append_system_prompt_file=data.get("append_system_prompt_file"),
        extra_binds=extra_binds,
        auto_memory_enabled=bool(data.get("auto_memory_enabled", False)),
    )

    if preset.name != preset_dir.name:
        raise ValueError(
            f"{yaml_path}: preset name {preset.name!r} does not match "
            f"directory name {preset_dir.name!r}"
        )
    return preset


