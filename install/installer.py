#!/usr/bin/env python3
"""Install the MadAgents agent system into a folder, to run without a container.

    python3 install/installer.py <target> [--memory PACK] [--no-git]
    python3 install/installer.py <target> --upgrade
    python3 install/installer.py --list-memory

The container path (``./madrun.sh``) and this one install the *same* agent
system; they differ only in what surrounds it. A run instance gets an image, an
overlay and a set of bind mounts, and the launcher supplies at start-up what
Claude Code cannot read from a directory — the lead's system prompt, the model,
where auto-memory lives. A native install has no launcher, so those have to be
written into the folder itself:

- the lead's system prompt becomes ``madagents.sh``, a wrapper that appends it;
- the auto-memory settings become ``.claude/settings.local.json``;
- the environment description becomes ``CLAUDE.md``, which Claude Code picks up
  from the project root on its own.

What the *container* install gets for free and this one cannot is MadGraph: an
image ships a known stack at a known path, while here MadGraph is wherever the
user has it, if they have it at all. So the seeded ``CLAUDE.md`` asserts no
location and asks the session to record what it finds — the same file the
container seeds, minus the claims only an image can make.

Layout produced::

    <target>/
      .claude/          agents, skills, the learned tier, settings.local.json
      .madagents/wiki/  the wiki half of the learned tier
      prompts/          the lead's system prompt, appended by the wrapper
      config.yaml       the configuration this install was built from
      CLAUDE.md         environment description — the session's to maintain
      madagents.sh      start a session here
      memory-pack.txt   which pack seeded this install

The target is a Claude Code *project root*: the roster's ``memory: project``
agents resolve their slates against it, which is the same reason the container
gives a run instance a git-initialised ``output/``.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from launcher.presets_loader import load_preset  # noqa: E402
from launcher.setup import (  # noqa: E402
    DEFAULT_MEMORY,
    DEFAULT_SYSTEM,
    NO_MEMORY,
    _copy_preset_tree,
    _resolve_memory_pack,
    memory_options,
)

#: What a memory pack contributes, as (path in the pack, path in the install).
#: The container puts the wiki under ``output/`` because that is its project
#: root; here the project root is the target itself, so the pack's own layout
#: transfers unchanged.
_MEMORY_TIERS = (
    (".claude/lead-memory", ".claude/lead-memory"),
    (".claude/agent-memory", ".claude/agent-memory"),
    (".madagents/wiki", ".madagents/wiki"),
)

#: Replaced by ``--upgrade``; everything else in the target is left alone.
#: These are the agent system as shipped — the parts a new release changes and
#: a session never writes to. The learned tier is deliberately not in the list.
_SYSTEM_PARTS = (".claude/agents", ".claude/skills", "prompts", "config.yaml")

#: Seed for the target's ``CLAUDE.md``, written only when there is none.
_ENV_TEMPLATE = Path(__file__).resolve().parent / "templates" / "CLAUDE.md"

WRAPPER_NAME = "madagents.sh"


def _fail(message: str, hint: str | None = None) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    if hint:
        print(f"  {hint}", file=sys.stderr)
    raise SystemExit(1)


def _copy_system(system_dir: Path, target: Path, parts: tuple[str, ...]) -> None:
    """Copy the shipped agent system into *target*, replacing *parts*."""
    for rel in parts:
        src = system_dir / rel
        if not src.exists():
            continue
        dst = target / rel
        if dst.exists():
            shutil.rmtree(dst) if dst.is_dir() else dst.unlink()
        dst.parent.mkdir(parents=True, exist_ok=True)
        _copy_preset_tree(src, dst)


def _seed_memory(pack: Path | None, target: Path) -> None:
    """Copy a pack's learned tier in, or lay down the empty layout for a cold start.

    Every tier is created either way, so the folder looks the same warm or cold
    and the session never has to create the directory it is about to write to.
    A tier the pack does not carry is empty, not inherited — the packs are
    starting points, and a half-inherited tier was never one of them.
    """
    for src_rel, dst_rel in _MEMORY_TIERS:
        dst = target / dst_rel
        if dst.exists():
            shutil.rmtree(dst)
        dst.parent.mkdir(parents=True, exist_ok=True)
        src = (pack / src_rel) if pack else None
        if src is not None and src.is_dir():
            _copy_preset_tree(src, dst)
        else:
            dst.mkdir()
    # The wiki's two halves, present cold so the layout does not depend on the pack.
    for half in ("consultants", "lead"):
        (target / ".madagents" / "wiki" / half).mkdir(parents=True, exist_ok=True)
    (target / "memory-pack.txt").write_text(
        f"{pack.name if pack else 'none'}\n"
        f"# Seeded by install/installer.py from "
        f"{pack if pack else 'no pack — cold start'}.\n"
        f"# This install owns its copy; the pack is unchanged. See memory/README.md.\n"
    )


def _write_settings(preset, target: Path) -> None:
    """Pin auto-memory on/off and point it at this folder's learned tier.

    The same two keys the container pins per instance, for the same two reasons:
    Claude Code merges ``autoMemoryEnabled`` over the user's own settings, so a
    user who turned it off globally would otherwise get an install whose 46
    consultant slates never load; and its default memory directory is under the
    user's Claude config, shared by every project, so the lead's slate — which
    has no ``memory: project`` card to place it — would be written outside this
    folder and lost to the next install.

    ``autoMemoryDirectory`` has to be absolute, which makes the folder
    non-relocatable. The wrapper re-points it on start rather than letting a
    moved folder silently lose its memory.
    """
    settings = target / ".claude" / "settings.local.json"
    try:
        data = json.loads(settings.read_text())
    except (OSError, json.JSONDecodeError):
        data = {}
    if not isinstance(data, dict):
        data = {}
    data["autoMemoryEnabled"] = bool(preset.auto_memory_enabled)
    if preset.auto_memory_enabled:
        data["autoMemoryDirectory"] = str(target / ".claude" / "lead-memory")
    else:
        data.pop("autoMemoryDirectory", None)
    settings.parent.mkdir(parents=True, exist_ok=True)
    settings.write_text(json.dumps(data, indent=2) + "\n")


def _append_prompt_paths(preset, system_dir: Path, target: Path) -> list[str]:
    """Target-relative paths of the system-prompt files the wrapper appends.

    ``append_system_prompt_file`` may name one file or several, resolved against
    the repo root. Files inside the shipped system are already in the target
    (they came with ``prompts/``); anything else is copied into ``prompts/`` so
    the install stays self-contained and keeps working if this repo moves.
    """
    configured = preset.append_system_prompt_file or []
    if isinstance(configured, str):
        configured = [configured]
    rels: list[str] = []
    for entry in configured:
        src = Path(entry)
        if not src.is_absolute():
            src = REPO_ROOT / src
        try:
            rel = src.resolve().relative_to(system_dir.resolve())
        except ValueError:
            dst = target / "prompts" / src.name
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            rels.append(f"prompts/{src.name}")
            continue
        if not (target / rel).is_file():
            _fail(f"system prompt {src} was not installed (expected at {target / rel})")
        rels.append(str(rel))
    return rels


def _write_wrapper(preset, target: Path, append_rels: list[str]) -> None:
    """Generate ``madagents.sh`` — the launcher's job, reduced to what applies here.

    Everything Claude Code can discover from a directory (the roster, the
    skills, ``CLAUDE.md``, the settings) is left to it. What it cannot — the
    appended system prompt, the model and effort from ``config.yaml`` — is
    baked in here, so a bare ``claude`` in this folder still works but the
    wrapper is what makes it the full system.
    """
    flags: list[str] = []
    for rel in append_rels:
        flags.append(f'--append-system-prompt "$(cat -- "{rel}")"')
    if preset.model:
        flags.append(f'--model "{preset.model}"')
    if preset.reasoning_effort:
        flags.append(f'--effort "{preset.reasoning_effort}"')
    if preset.disallowed_tools:
        joined = " ".join(f'"{t}"' for t in preset.disallowed_tools)
        flags.append(f"--disallowed-tools {joined}")
    flag_text = " \\\n     ".join(flags)

    missing_checks = "\n".join(
        f'[[ -f "{rel}" ]] || {{ echo "ERROR: {rel} is missing — reinstall." >&2; exit 1; }}'
        for rel in append_rels
    )

    wrapper = f"""#!/usr/bin/env bash
# MadAgents — start a session on the agent system installed in this folder.
#
#   ./{WRAPPER_NAME}              start a session
#   ./{WRAPPER_NAME} --resume     anything unrecognised is forwarded to claude
#
# What this adds over a bare `claude` here: the lead's system prompt, and the
# model settings this system was configured with. The roster, the skills, the
# learned tier and CLAUDE.md are picked up from this directory by Claude Code
# itself. Generated by install/installer.py — re-running the installer with
# --upgrade regenerates it.
set -euo pipefail
HERE="$(cd -- "$(dirname -- "${{BASH_SOURCE[0]}}")" && pwd)"
cd -- "$HERE"

{missing_checks}

# Auto-memory is pinned by ABSOLUTE path (Claude Code requires one), so moving
# this folder would silently detach the learned tier — the 46 consultant slates
# and the lead's — and the session would come up cold without saying so.
# Re-point it here instead, every start, so a moved install just works.
if command -v python3 >/dev/null 2>&1; then
  python3 - "$HERE" <<'PY' || true
import json, sys
from pathlib import Path

here = Path(sys.argv[1])
settings = here / ".claude" / "settings.local.json"
try:
    data = json.loads(settings.read_text())
except Exception:
    sys.exit(0)
if not isinstance(data, dict) or not data.get("autoMemoryEnabled"):
    sys.exit(0)
want = str(here / ".claude" / "lead-memory")
if data.get("autoMemoryDirectory") != want:
    data["autoMemoryDirectory"] = want
    settings.write_text(json.dumps(data, indent=2) + "\\n")
    print(f"madagents: this folder moved — auto-memory re-pointed at {{want}}")
PY
fi

exec claude {flag_text} "$@"
"""
    path = target / WRAPPER_NAME
    path.write_text(wrapper)
    path.chmod(0o755)


def _seed_environment(target: Path) -> None:
    """Seed ``CLAUDE.md``, the environment description, when there is none.

    Written once and never again: from here on it is the session's file, to
    correct and extend as it learns where things actually are. That is the whole
    point of it — on a user's own machine nothing can be assumed about where
    MadGraph lives, so the description has to be earned rather than declared.
    """
    target_file = target / "CLAUDE.md"
    if target_file.exists():
        return
    try:
        text = _ENV_TEMPLATE.read_text(encoding="utf-8")
    except OSError:
        return
    target_file.write_text(text, encoding="utf-8")


def _git_init(target: Path) -> None:
    """Make the target its own git repo, so it is a deterministic project root.

    Claude Code resolves the project root to the enclosing git repository when
    there is one. Without this, installing inside an existing repo would put the
    project root at *that* repo's top, and every ``memory: project`` slate would
    be read from and written to a ``.claude/`` that is not this install's. A
    nested repo is exactly how the container gets the same guarantee for its
    ``output/``.
    """
    if (target / ".git").exists():
        return
    try:
        subprocess.run(["git", "init", "-q", str(target)], check=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        print(
            f"WARNING: could not git-init {target} ({exc}). If this folder sits "
            f"inside another git repository, Claude Code will resolve the "
            f"project root to that repository and the learned tier will not load.",
            file=sys.stderr,
        )


def _print_memory_options() -> None:
    for name, description in memory_options():
        print(f"  {name:18s} {description}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="installer.py",
        description="Install the MadAgents agent system into a folder (no container).",
    )
    parser.add_argument("target", nargs="?", help="folder to install into")
    parser.add_argument(
        "--memory", default=None,
        help="memory pack to seed, or 'none' for a cold start (default: "
             f"{DEFAULT_MEMORY})",
    )
    parser.add_argument(
        "--upgrade", action="store_true",
        help="replace the shipped agent system in an existing install, keeping "
             "its learned tier, CLAUDE.md and memory pack",
    )
    parser.add_argument(
        "--no-git", action="store_true",
        help="skip git init (only if the folder is already its own repo root)",
    )
    parser.add_argument(
        "--list-memory", action="store_true", help="list memory packs and exit",
    )
    args = parser.parse_args(argv)

    if args.list_memory:
        _print_memory_options()
        return 0
    if not args.target:
        parser.error("target is required (or pass --list-memory)")

    system_dir = DEFAULT_SYSTEM
    if not (system_dir / "config.yaml").is_file():
        _fail(f"agent system not found at {system_dir}",
              "Run this from a MadAgents checkout.")
    preset = load_preset(system_dir)

    target = Path(args.target).expanduser().resolve()
    installed = (target / ".claude").exists()

    if args.upgrade:
        if not installed:
            _fail(f"nothing installed at {target}",
                  "Drop --upgrade to install here for the first time.")
        if args.memory is not None:
            _fail("--upgrade keeps the existing learned tier, so --memory does not apply",
                  "Install into a fresh folder to start from a different pack.")
    elif installed:
        _fail(f"{target / '.claude'} already exists",
              "Use --upgrade to refresh the agent system there, or pick another folder.")

    memory_name = args.memory if args.memory is not None else DEFAULT_MEMORY
    pack = None
    if not args.upgrade and memory_name.lower() not in NO_MEMORY:
        pack = _resolve_memory_pack(memory_name)

    target.mkdir(parents=True, exist_ok=True)
    print(f"madagents install: {'upgrading' if args.upgrade else 'installing'} "
          f"{preset.name!r} → {target}")

    _copy_system(system_dir, target, _SYSTEM_PARTS)
    if not args.upgrade:
        _seed_memory(pack, target)
    _write_settings(preset, target)
    _write_wrapper(preset, target, _append_prompt_paths(preset, system_dir, target))
    _seed_environment(target)
    if not args.no_git:
        _git_init(target)

    n_agents = len(list((target / ".claude" / "agents").glob("*.md")))
    n_skills = len([d for d in (target / ".claude" / "skills").iterdir() if d.is_dir()])
    if args.upgrade:
        print(f"madagents install: agent system replaced ({n_agents} agents, "
              f"{n_skills} skills); learned tier untouched")
    else:
        slates = target / ".claude" / "agent-memory"
        n_slates = len([d for d in slates.iterdir() if d.is_dir()]) if slates.is_dir() else 0
        n_pages = len(list((target / ".madagents" / "wiki").rglob("*.md")))
        print(f"madagents install: {n_agents} agents, {n_skills} skills, "
              f"memory {pack.name if pack else 'none'} "
              f"({n_slates} slates, {n_pages} wiki pages)")
    print(f"madagents install: start it with  cd {target} && ./{WRAPPER_NAME}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
