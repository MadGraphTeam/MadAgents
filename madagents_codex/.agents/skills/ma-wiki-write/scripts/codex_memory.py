"""The Codex learned tier — a consultant's slate, inside its own role file.

Claude Code auto-loads a consultant's slate from
``.claude/agent-memory/<name>/MEMORY.md`` because the card declares
``memory: project``. Codex has no such key; what it has is
``developer_instructions``, a **required** field of every custom agent file
(``.codex/agents/<name>.toml``), which Codex applies as a configuration layer
to every spawn of that role. That is the same guarantee by a different route:
always loaded, no tool call, no reliance on the agent choosing to read
anything.

So on Codex a role file carries *both* halves — the card body, and the slate
appended below it between two markers::

    developer_instructions = '''
    # Physics Consultant
    ... the card ...

    <!-- MADAGENTS-SLATE:BEGIN -->
    ## Slice
    ... the slate ...
    <!-- MADAGENTS-SLATE:END -->
    '''

This module owns that marked region: :func:`read_slate` and
:func:`write_slate`, plus :func:`seed_slates` for laying a memory pack down
over a freshly rendered tree. Three callers share it — the run-instance
harness, the folder installer, and the ``write_slate.py`` script bundled with
the ``ma-wiki-write`` skill, which is how an agent edits its own slate at
runtime.

**Why an agent never hand-edits the TOML.** A malformed role file is dropped
from the registry outright (Codex logs "Ignoring malformed agent role
definition" and moves on), which would take the consultant's *card* down with
its slate — a failure with no symptom except a consultant that has silently
stopped existing. Claude Code has the same cliff for malformed YAML
frontmatter, which is why ``lead-discipline.md`` warns about it; here the blast
radius is larger, so the write goes through :func:`write_slate`, which edits
the raw text between the markers and then re-parses the whole file before
letting the result replace the original.
"""
from __future__ import annotations

import os
import tomllib
from pathlib import Path

#: Markers bounding the agent-owned region of ``developer_instructions``.
#: HTML comments: invisible in rendered markdown, unambiguous to match, and
#: legible to the agent itself — it can see exactly which region is its own.
SLATE_BEGIN = "<!-- MADAGENTS-SLATE:BEGIN -->"
SLATE_END = "<!-- MADAGENTS-SLATE:END -->"

#: Fixed prose the renderer places above the markers, so the agent knows what
#: the region is and how to write it. Not inside the markers: it is shipped
#: system text, not learned state, and must survive every slate rewrite.
SLATE_PREAMBLE = """
---

# Your slate — auto-loaded memory

Everything between the two markers below is **yours**: the same slate Claude Code would auto-load,
carried here because Codex delivers a role's standing instructions through this file. It is loaded
on every dispatch of you, so treat it as always-in-context and keep it to its ~80-line budget.

Write it with `/ma-wiki-write`, which calls `scripts/write_slate.py`. **Never hand-edit this file**
— it is TOML, and a malformed edit removes you from the roster entirely, card and all.
""".strip()

#: TOML multi-line *literal* strings (''' … ''') take no escapes, which is what
#: keeps LaTeX backslashes in the physics cards verbatim. The one thing they
#: cannot contain is the delimiter itself.
_TOML_LITERAL_DELIM = "'''"

#: What a cold slate holds — the section skeleton from ma-wiki-write's "slate
#: shape", so a cold agent extends a structure rather than inventing one.
COLD_SLATE = """## Slice

## Core operating principles

## Recent lessons (FIFO, max 5)

## Wiki page index
"""


#: The lead's slate, relative to the project root. Consultants carry theirs
#: inside their own role file; the lead has no role file, so its slate stays an
#: ordinary markdown file and is appended to the lead's prompt at start-up.
LEAD_SLATE_REL = ".madagents/memory/lead/MEMORY.md"


def lead_slate_header() -> str:
    """The heading that introduces the lead's slate in its appended prompt.

    Shared by the two things that compose that prompt — the container launcher
    and the generated ``madagents.sh`` — so the lead is told the same thing
    about its own memory either way.
    """
    return (
        "---\n\n# Your slate — auto-loaded memory\n\n"
        f"Maintained by you with `/ma-wiki-write`, which writes `{LEAD_SLATE_REL}`. "
        "Edits land in the next session, so treat this as what you knew at start-up."
    )


class SlateError(RuntimeError):
    """A role file could not be read or written as a slate carrier."""


def role_path(agents_dir: Path, agent_name: str) -> Path:
    """Path to *agent_name*'s role file. Filename mirrors the agent name."""
    return agents_dir / f"{agent_name}.toml"


def validate_slate_text(slate: str) -> None:
    """Reject slate text that cannot survive a TOML literal string.

    The only hard constraint is the delimiter. Raising here — rather than at
    write time, halfway through replacing a file — is what lets the caller
    surface a usable message instead of a corrupted role.
    """
    if _TOML_LITERAL_DELIM in slate:
        raise SlateError(
            f"slate contains {_TOML_LITERAL_DELIM!r}, which would terminate the TOML "
            f"literal string that carries it. Remove or reword that sequence."
        )


def _split(text: str, path: Path) -> tuple[str, str, str]:
    """Split raw role-file text into (before, slate, after) around the markers."""
    start = text.find(SLATE_BEGIN)
    end = text.find(SLATE_END)
    if start == -1 or end == -1:
        raise SlateError(
            f"{path}: no slate region — expected {SLATE_BEGIN} … {SLATE_END}. "
            f"Re-render the Codex tree with tools/render_codex.py."
        )
    if end < start:
        raise SlateError(f"{path}: slate markers are in the wrong order")
    body_start = start + len(SLATE_BEGIN)
    return text[:body_start], text[body_start:end], text[end:]


def read_slate(path: Path) -> str:
    """Return *path*'s slate markdown, without the markers."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SlateError(f"{path}: cannot read ({exc})") from exc
    return _split(text, path)[1].strip("\n")


def write_slate(path: Path, slate: str) -> None:
    """Replace *path*'s slate with *slate*, or raise without touching the file.

    Deliberately a text-level substitution rather than a parse-and-re-emit:
    the stdlib can read TOML but not write it, and re-emitting would reflow the
    whole role file — a large diff on every slate write, and one more thing to
    get wrong in the card half that this function has no business editing.

    The safety comes from checking afterwards instead: the result is parsed as
    TOML and the slate is read back out of the parsed value before anything is
    written to disk. So a write either lands intact or does not happen.
    """
    validate_slate_text(slate)
    try:
        original = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SlateError(f"{path}: cannot read ({exc})") from exc

    before, _, after = _split(original, path)
    body = slate.strip("\n")
    updated = f"{before}\n{body}\n{after}" if body else f"{before}\n{after}"

    # Parse the whole file, not just the region: the check has to catch a
    # slate that is individually fine but breaks the file it lands in.
    try:
        parsed = tomllib.loads(updated)
    except tomllib.TOMLDecodeError as exc:
        raise SlateError(
            f"{path}: the new slate would make this file invalid TOML ({exc}). "
            f"File left unchanged."
        ) from exc
    for key in ("name", "description", "developer_instructions"):
        if not parsed.get(key):
            raise SlateError(
                f"{path}: writing the slate would leave {key!r} missing or empty. "
                f"File left unchanged."
            )
    # And confirm the slate is actually reachable through the parsed value —
    # a substitution that landed outside developer_instructions would still
    # parse, and would still be silently inert at runtime.
    if body and body not in parsed["developer_instructions"]:
        raise SlateError(
            f"{path}: the slate did not land inside developer_instructions. "
            f"File left unchanged."
        )

    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(updated, encoding="utf-8")
    os.replace(tmp, path)


def seed_slates(agents_dir: Path, agent_memory_dir: Path) -> tuple[int, int]:
    """Lay a memory pack's slates into a rendered Codex tree.

    The packs in ``memory/`` are provider-neutral and stay in their Claude Code
    shape — ``<pack>/.claude/agent-memory/<name>/MEMORY.md``. This is where
    that shape is translated for Codex, so one pack keeps serving both
    providers and a pack never has to know which one seeded it.

    A role with no slate in the pack is left at whatever the render gave it
    (the cold skeleton), which is what makes a partial pack mean "cold for the
    rest" rather than "half-inherited".

    Returns ``(seeded, skipped)`` — slates written, and pack entries with no
    matching role file.
    """
    if not agent_memory_dir.is_dir():
        return (0, 0)
    seeded = skipped = 0
    for slate_dir in sorted(p for p in agent_memory_dir.iterdir() if p.is_dir()):
        slate_file = slate_dir / "MEMORY.md"
        if not slate_file.is_file():
            continue
        target = role_path(agents_dir, slate_dir.name)
        if not target.is_file():
            # A pack accumulated against an older roster naming an agent this
            # render no longer has. Report it; do not invent a role file, which
            # would resurrect a consultant the system deliberately dropped.
            skipped += 1
            continue
        write_slate(target, slate_file.read_text(encoding="utf-8"))
        seeded += 1
    return (seeded, skipped)


def has_content(slate: str) -> bool:
    """True when a slate holds something beyond the empty section skeleton.

    Every role ships with the headings in place, so "the region is non-empty"
    would count a cold roster as fully seeded and report 46 slates on a cold
    start. What counts is a line that is neither blank nor a heading.
    """
    return any(
        line.strip() and not line.lstrip().startswith("#")
        for line in slate.splitlines()
    )


def count_seeded(agents_dir: Path) -> int:
    """Role files whose slate holds learned content — for the setup/install summary."""
    total = 0
    for path in sorted(agents_dir.glob("*.toml")):
        try:
            if has_content(read_slate(path)):
                total += 1
        except SlateError:
            continue
    return total
