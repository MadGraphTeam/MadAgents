#!/usr/bin/env python3
"""Verify a MadAgents install. Read-only — this file writes nothing, ever.

    python3 install/installer.py verify <target> [--allow-modified]

**Installing is the agent's job.** It used to be this script's, and that was the
bug: a script cannot tell a MadAgents install from someone's own project, so it
guessed — ``.claude/`` exists — and then ``--upgrade`` ``rmtree``d
``.claude/agents`` and ``.claude/skills``, taking the host project's own agents
and skills with it. The judgment ("is this a host project? what collides? should
this folder become a git root?") moved into the install skill, which can look at
the folder and ask. What is left here is the half a model should not be trusted
with alone: proving the result is intact.

It checks the failures that are **silent**, because the loud ones report
themselves:

- a role TOML that does not parse — the consultant is dropped from the roster
  with no error, and nothing ever says so;
- a skill whose ``description:`` is not valid YAML — Codex drops the skill
  silently, so it simply never fires;
- a slate region that went missing — the learned tier is gone and the session
  comes up cold without mentioning it;
- a file that was transcribed instead of copied — subtly wrong, never flagged;
- **a pre-existing host file that the install overwrote** — the regression that
  motivated all of this.

The last one needs a baseline, so the install skill records one: the manifest's
``preexisting`` map is a hash of every file in the collision surface *before*
anything was written. Without it that check is skipped, and says so.

The manifest (``<target>/.madagents/install.json``) is what makes any of this
possible. It is also what replaces the old detection heuristic: a folder is a
MadAgents install if and only if it has one.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tomllib
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from launcher import codex_memory  # noqa: E402
from launcher.presets_loader import load_preset  # noqa: E402
from launcher.setup import SYSTEM_BY_PROVIDER  # noqa: E402

MANIFEST_REL = ".madagents/install.json"
MANIFEST_SCHEMA = 1
WRAPPER_NAME = "madagents.sh"
TEMPLATES = Path(__file__).resolve().parent / "templates"

#: Where an install can collide with a host project. The skill hashes exactly
#: these before writing, so ``preexisting`` stays bounded on a large repo
#: instead of inventorying the whole tree.
COLLISION_SURFACE = (
    ".claude", ".codex", ".agents", ".madagents",
    "prompts", "CLAUDE.md", "AGENTS.md", WRAPPER_NAME,
    "config.yaml", "memory-pack.txt",
)

EXPECTED_ROLES = 46
EXPECTED_SKILLS = 8


class Report:
    """Collects check results. Any failure makes the whole run exit non-zero."""

    def __init__(self) -> None:
        self.failed = 0
        self.warned = 0

    def ok(self, msg: str) -> None:
        print(f"  ok    {msg}")

    def warn(self, msg: str) -> None:
        self.warned += 1
        print(f"  warn  {msg}")

    def fail(self, msg: str) -> None:
        self.failed += 1
        print(f"  FAIL  {msg}")

    def skip(self, msg: str) -> None:
        print(f"  skip  {msg}")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hash_surface(target: Path) -> dict[str, str]:
    """Hash every file in the collision surface. Used to build ``preexisting``.

    Exposed so the install skill can produce the baseline with the same
    definition this file later checks against — one source of truth for what
    "the collision surface" means.
    """
    out: dict[str, str] = {}
    for rel in COLLISION_SURFACE:
        entry = target / rel
        if entry.is_file():
            out[rel] = sha256(entry)
        elif entry.is_dir():
            for p in sorted(entry.rglob("*")):
                if p.is_file():
                    out[str(p.relative_to(target))] = sha256(p)
    return out


def render_wrapper(template: str, prompt_files: list[str],
                   disallowed_tools: list[str]) -> str:
    """Substitute the wrapper template's two arrays.

    The install skill produces the wrapper with exactly this substitution (as a
    two-expression ``sed``), so verify can regenerate what the wrapper *should*
    be and compare byte-for-byte. That turns the highest-risk generated file
    into an exact check rather than a structural guess.

    The rule is uniform: a placeholder line becomes zero or more quoted entries,
    one per line. Zero entries leaves an empty array literal, which is valid.
    """
    def block(items: list[str]) -> list[str]:
        return [f'  "{i}"' for i in items]

    out: list[str] = []
    for line in template.splitlines():
        if line == "@@PROMPT_FILES@@":
            out.extend(block(prompt_files))
        elif line == "@@DISALLOWED_TOOLS@@":
            out.extend(block(disallowed_tools))
        else:
            out.append(line)
    return "\n".join(out) + "\n"


def load_manifest(target: Path, rep: Report) -> dict | None:
    path = target / MANIFEST_REL
    if not path.is_file():
        rep.fail(f"no manifest at {MANIFEST_REL} — this folder is not a MadAgents install")
        return None
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        rep.fail(f"{MANIFEST_REL} is unreadable: {exc}")
        return None
    if data.get("schema") != MANIFEST_SCHEMA:
        rep.fail(f"{MANIFEST_REL}: schema {data.get('schema')!r}, expected {MANIFEST_SCHEMA}")
        return None
    if data.get("provider") not in SYSTEM_BY_PROVIDER:
        rep.fail(f"{MANIFEST_REL}: unknown provider {data.get('provider')!r}")
        return None
    rep.ok(f"manifest: {data['provider']} install, memory pack "
           f"{data.get('memory_pack', 'unrecorded')!r}")
    return data


def check_copies(target: Path, manifest: dict, source: Path, rep: Report,
                 allow_modified: bool) -> None:
    """Every byte-copied file is present and identical to what shipped."""
    paths = manifest.get("paths") or {}
    if not paths:
        rep.fail("manifest records no copied paths")
        return
    missing, changed = [], []
    for rel, recorded in sorted(paths.items()):
        installed = target / rel
        if not installed.is_file():
            missing.append(rel)
            continue
        if sha256(installed) != recorded:
            changed.append(rel)
    if missing:
        rep.fail(f"{len(missing)} recorded file(s) missing, e.g. {missing[0]}")
    if changed:
        note = f"{len(changed)} file(s) differ from what was installed, e.g. {changed[0]}"
        rep.warn(note + " (expected if the system has edited itself)") if allow_modified \
            else rep.fail(note)
    if not missing and not changed:
        rep.ok(f"{len(paths)} copied file(s) present and unmodified")

    # Against the shipped source: catches a bad copy at install time, and
    # distinguishes it from a later self-edit.
    #
    # Codex role files are excluded: a warm install splices the pack's slate
    # into each one, so differing from the shipped file is exactly what a
    # seeded roster looks like. Their integrity is checked by check_roles
    # instead, which is the check that actually matters for them.
    stale = [rel for rel in paths
             if not rel.startswith(".codex/agents/")
             and (source / rel).is_file() and paths[rel] != sha256(source / rel)]
    if stale:
        rep.warn(f"{len(stale)} file(s) differ from the current shipped system "
                 f"(e.g. {stale[0]}) — upgrade available, or the copy was not byte-exact")
    else:
        rep.ok("copied files match the shipped system")


def check_preexisting(target: Path, manifest: dict, rep: Report) -> None:
    """Nothing the install did not own was overwritten or removed."""
    baseline = manifest.get("preexisting")
    if baseline is None:
        rep.skip("no pre-install baseline recorded — cannot prove host files survived")
        return
    owned = set(manifest.get("paths") or {}) | set(manifest.get("generated") or [])
    consented = set(manifest.get("replaced_with_consent") or [])

    # A path that existed BEFORE and is now claimed as ours was overwritten. The
    # policy says every such collision is named to the user before anything is
    # written, so the manifest has to record that it was — otherwise "I own this
    # file" would silently excuse having clobbered it, and the whole baseline
    # check could be defeated by over-claiming.
    unconsented = sorted((set(baseline) & owned) - consented)
    if unconsented:
        rep.fail(f"{len(unconsented)} pre-existing file(s) were replaced without being "
                 f"recorded as agreed, e.g. {unconsented[0]} — either the user was not "
                 f"asked, or the install over-claimed ownership")

    clobbered, removed = [], []
    for rel, recorded in sorted(baseline.items()):
        if rel in owned:
            continue  # replaced; handled by the consent check above
        entry = target / rel
        if not entry.is_file():
            removed.append(rel)
        elif sha256(entry) != recorded:
            clobbered.append(rel)
    if removed:
        rep.fail(f"{len(removed)} pre-existing file(s) were REMOVED, e.g. {removed[0]}")
    if clobbered:
        rep.fail(f"{len(clobbered)} pre-existing file(s) were OVERWRITTEN, e.g. {clobbered[0]}")
    if not removed and not clobbered:
        rep.ok(f"all {len(baseline)} pre-existing file(s) intact")


def check_roles(target: Path, source: Path, rep: Report) -> None:
    """Codex roles parse, are named for their file, and kept their slate region.

    Not every role has one: the reviewer/auditor cards carry no ``memory:`` on
    the Claude Code side, so the renderer gives them no slate block either. The
    shipped tree is therefore the authority on which roles *should* have a
    slate — demanding one from all 46 would fail a perfectly good install.
    """
    agents = target / ".codex" / "agents"
    if not agents.is_dir():
        rep.fail(".codex/agents/ is missing — the roster does not exist")
        return
    roles = sorted(agents.glob("*.toml"))
    bad_toml, bad_name, missing_field, bad_slate = [], [], [], []
    for role in roles:
        try:
            data = tomllib.loads(role.read_text())
        except (OSError, tomllib.TOMLDecodeError):
            bad_toml.append(role.name)
            continue
        if data.get("name") != role.stem:
            bad_name.append(role.name)
        if not data.get("description") or not data.get("developer_instructions"):
            missing_field.append(role.name)
        shipped = source / ".codex" / "agents" / role.name
        if not shipped.is_file():
            continue  # a role this release does not ship; nothing to compare to
        try:
            codex_memory.read_slate(shipped)
        except codex_memory.SlateError:
            continue  # slate-less by design (reviewer/auditor)
        try:
            codex_memory.read_slate(role)
        except codex_memory.SlateError:
            bad_slate.append(role.name)
    for label, items in (("do not parse as TOML", bad_toml),
                         ("have name != filename", bad_name),
                         ("lack description/developer_instructions", missing_field)):
        if items:
            rep.fail(f"{len(items)} role file(s) {label} — those consultants do not "
                     f"exist, silently: {', '.join(items[:3])}")
    if bad_slate:
        rep.fail(f"{len(bad_slate)} role file(s) have no readable slate region — the "
                 f"learned tier is gone for them: {', '.join(bad_slate[:3])}")
    if not (bad_toml or bad_name or missing_field or bad_slate):
        rep.ok(f"{len(roles)} role file(s) parse, are correctly named, and carry a slate")
    if len(roles) != EXPECTED_ROLES:
        rep.warn(f"{len(roles)} roles installed, expected {EXPECTED_ROLES}")


def check_skills(target: Path, is_codex: bool, rep: Report) -> None:
    """Skill frontmatter is valid YAML with a description.

    The failure this exists for: an unquoted ``": "`` inside ``description:``
    makes the frontmatter invalid YAML, and Codex then drops the skill without
    a word. Claude Code tolerates it, so the same tree can work on one provider
    and be quietly short a skill on the other.
    """
    root = target / (".agents" if is_codex else ".claude") / "skills"
    if not root.is_dir():
        rep.fail(f"{root.relative_to(target)}/ is missing — no skills installed")
        return
    skills = sorted(d for d in root.iterdir() if d.is_dir())
    bad, no_desc = [], []
    for skill in skills:
        md = skill / "SKILL.md"
        if not md.is_file():
            bad.append(f"{skill.name} (no SKILL.md)")
            continue
        text = md.read_text()
        if not text.startswith("---\n") or "\n---\n" not in text[4:]:
            bad.append(f"{skill.name} (no frontmatter)")
            continue
        front = text[4:].split("\n---\n", 1)[0]
        try:
            data = yaml.safe_load(front)
        except yaml.YAMLError:
            bad.append(f"{skill.name} (invalid YAML)")
            continue
        if not isinstance(data, dict) or not data.get("description"):
            no_desc.append(skill.name)
    if bad:
        rep.fail(f"{len(bad)} skill(s) have unreadable frontmatter — dropped "
                 f"silently: {', '.join(bad[:3])}")
    if no_desc:
        rep.fail(f"{len(no_desc)} skill(s) have no description — never routed to: "
                 f"{', '.join(no_desc[:3])}")
    if not bad and not no_desc:
        rep.ok(f"{len(skills)} skill(s) have valid frontmatter with a description")
    if len(skills) != EXPECTED_SKILLS:
        rep.warn(f"{len(skills)} skills installed, expected {EXPECTED_SKILLS}")


def check_wrapper(target: Path, manifest: dict, is_codex: bool, rep: Report) -> None:
    """The wrapper is exactly the template plus the recorded substitutions."""
    wrapper = target / WRAPPER_NAME
    if not wrapper.is_file():
        rep.fail(f"{WRAPPER_NAME} is missing — nothing starts the full system")
        return
    if not wrapper.stat().st_mode & 0o111:
        rep.fail(f"{WRAPPER_NAME} is not executable")
    template = TEMPLATES / ("madagents-codex.sh" if is_codex else "madagents.sh")
    expected = render_wrapper(
        template.read_text(),
        manifest.get("prompt_files") or [],
        manifest.get("disallowed_tools") or [],
    )
    if wrapper.read_text() != expected:
        rep.fail(f"{WRAPPER_NAME} does not match {template.name} with the recorded "
                 f"substitutions — it was edited or assembled by hand")
    else:
        rep.ok(f"{WRAPPER_NAME} matches {template.name} exactly")
    for rel in manifest.get("prompt_files") or []:
        if not (target / rel).is_file():
            rep.fail(f"{WRAPPER_NAME} starts the lead with {rel}, which does not exist")


def check_codex_extras(target: Path, rep: Report) -> None:
    """The two Codex-only things that fail silently when absent."""
    header = target / "prompts" / "lead-slate-header.md"
    if not header.is_file():
        rep.fail("prompts/lead-slate-header.md is missing — the wrapper aborts once "
                 "the lead has written a slate")
    elif header.read_text().rstrip("\n") != codex_memory.lead_slate_header().rstrip("\n"):
        rep.warn("prompts/lead-slate-header.md differs from the shipped header")
    else:
        rep.ok("lead slate header matches the shipped text")

    # Trust is what decides whether .codex/ is read at all. Untrusted, the
    # roster silently does not exist — the single most confusing Codex failure.
    # Honour CODEX_HOME the way Codex itself does; assuming ~/.codex reports a
    # missing config on any host that relocates it.
    codex_home = Path(os.environ.get("CODEX_HOME") or (Path.home() / ".codex"))
    config = codex_home / "config.toml"
    resolved = str(target.resolve())
    if not config.is_file():
        rep.warn(f"no {config} — trust this folder on the first `codex` run, or the "
                 f"roster will silently not exist")
        return
    try:
        projects = tomllib.loads(config.read_text()).get("projects", {})
    except (OSError, tomllib.TOMLDecodeError):
        rep.warn(f"{config} does not parse; cannot confirm this folder is trusted")
        return
    entry = projects.get(resolved) or {}
    if entry.get("trust_level") == "trusted":
        rep.ok("project is recorded as trusted in $CODEX_HOME/config.toml")
    else:
        rep.warn(f"{resolved} is not recorded as trusted — answer yes on the first "
                 f"`codex` run here, or .codex/ is ignored entirely")


def check_claude_memory(target: Path, rep: Report) -> None:
    """Auto-memory is on and points inside this folder."""
    settings = target / ".claude" / "settings.local.json"
    if not settings.is_file():
        rep.fail(".claude/settings.local.json is missing — the lead's slate will be "
                 "written outside this folder and lost")
        return
    try:
        data = json.loads(settings.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        rep.fail(f".claude/settings.local.json does not parse: {exc}")
        return
    if not data.get("autoMemoryEnabled"):
        rep.fail("autoMemoryEnabled is not set — the 46 consultant slates will not load")
        return
    want = str(target / ".claude" / "lead-memory")
    got = data.get("autoMemoryDirectory")
    if got != want:
        rep.fail(f"autoMemoryDirectory is {got!r}, expected {want!r} — the lead's slate "
                 f"would be read from somewhere else")
    else:
        rep.ok("auto-memory is enabled and points at this folder's lead-memory")


def cmd_verify(target: Path, allow_modified: bool) -> int:
    if not target.is_dir():
        print(f"ERROR: {target} is not a directory", file=sys.stderr)
        return 2
    print(f"madagents verify: {target}")
    rep = Report()

    manifest = load_manifest(target, rep)
    if manifest is None:
        print("\n1 check failed. Nothing else could be checked without a manifest.")
        return 1

    provider = manifest["provider"]
    is_codex = provider == "codex"
    source = SYSTEM_BY_PROVIDER[provider]

    check_copies(target, manifest, source, rep, allow_modified)
    check_preexisting(target, manifest, rep)
    check_skills(target, is_codex, rep)
    check_wrapper(target, manifest, is_codex, rep)
    if is_codex:
        check_roles(target, source, rep)
        check_codex_extras(target, rep)
    else:
        check_claude_memory(target, rep)

    print()
    if rep.failed:
        print(f"{rep.failed} check(s) FAILED, {rep.warned} warning(s). "
              f"This install is not sound.")
        return 1
    print(f"All checks passed ({rep.warned} warning(s)).")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify a MadAgents install. Read-only — writes nothing.",
        epilog="Installing is the agent's job: run `claude` or `codex` in install/.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    v = sub.add_parser("verify", help="check that an install is intact")
    v.add_argument("target", help="the installed folder")
    v.add_argument("--allow-modified", action="store_true",
                   help="treat a changed system file as a warning, not a failure "
                        "(use once the system has begun editing itself)")
    args = parser.parse_args(argv)
    return cmd_verify(Path(args.target).expanduser().resolve(), args.allow_modified)


if __name__ == "__main__":
    raise SystemExit(main())
