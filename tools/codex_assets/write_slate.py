#!/usr/bin/env python3
"""Write a consultant's slate — the one safe way to edit a role file.

    python3 scripts/write_slate.py --agent <name> --show
    python3 scripts/write_slate.py --agent <name> --file new-slate.md
    python3 scripts/write_slate.py --agent <name> --stdin   < new-slate.md

On Codex a consultant's slate lives inside its own role file
(``.codex/agents/<name>.toml``), because ``developer_instructions`` is what
Codex auto-loads into every dispatch of that role. That makes the slate always
in context — and it also means an edit that breaks the TOML removes the
consultant from the roster entirely, card and all, with no error the session
will notice.

So slates are not hand-edited. This script replaces only the marked region,
re-parses the whole file, and keeps the original unless the result is valid.
``--show`` prints the current slate, which is how you read before you rewrite.

Bundled with the ``ma-wiki-write`` skill; copied here by
``tools/render_codex.py`` alongside the module it uses.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from codex_memory import SlateError, read_slate, role_path, write_slate  # noqa: E402


def find_agents_dir(start: Path) -> Path | None:
    """Walk up from *start* looking for the project's ``.codex/agents``."""
    for candidate in (start, *start.parents):
        agents = candidate / ".codex" / "agents"
        if agents.is_dir():
            return agents
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="write_slate.py",
        description="Read or replace a consultant's slate inside its role file.",
    )
    parser.add_argument("--agent", required=True, help="agent name, e.g. ma-physics-consultant")
    parser.add_argument("--agents-dir", default=None, help="override .codex/agents discovery")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--show", action="store_true", help="print the current slate and exit")
    source.add_argument("--file", default=None, help="read the new slate from this file")
    source.add_argument("--stdin", action="store_true", help="read the new slate from stdin")
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    if args.agents_dir:
        agents_dir = Path(args.agents_dir).expanduser().resolve()
    else:
        found = find_agents_dir(Path.cwd())
        if found is None:
            print(
                "write_slate: no .codex/agents/ found from this directory upward. "
                "Run from inside the project, or pass --agents-dir.",
                file=sys.stderr,
            )
            return 2
        agents_dir = found

    path = role_path(agents_dir, args.agent)
    if not path.is_file():
        available = sorted(p.stem for p in agents_dir.glob("*.toml"))
        print(f"write_slate: no role file at {path}", file=sys.stderr)
        print(f"  available: {', '.join(available) or '(none)'}", file=sys.stderr)
        return 2

    try:
        if args.show or not (args.file or args.stdin):
            print(read_slate(path))
            return 0
        new = sys.stdin.read() if args.stdin else Path(args.file).read_text(encoding="utf-8")
        write_slate(path, new)
    except SlateError as exc:
        print(f"write_slate: {exc}", file=sys.stderr)
        return 1

    lines = len(new.strip().splitlines())
    note = "" if lines <= 80 else "  WARNING: over the ~80-line slate budget — demote something."
    print(f"write_slate: {args.agent} slate updated ({lines} lines).{note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
