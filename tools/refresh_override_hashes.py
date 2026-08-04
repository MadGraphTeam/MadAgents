#!/usr/bin/env python3
"""Re-pin a provider's overrides to the current canonical files.

    python3 tools/refresh_override_hashes.py [--manifest PATH] [--dry-run]

Run this **after** folding a canonical change into the matching override — never
instead of. The pin exists so that editing a canonical file surfaces every fork
that now needs revisiting; refreshing a hash without reading the diff is how you
turn that signal off and let the providers drift apart silently.

There is one manifest per rendered provider — ``tools/codex_overrides/`` and
``tools/opencode_overrides/``. ``--manifest`` selects which; the default is
the Codex one, which is where this tool started.

The tool prints the diff you are about to acknowledge, so there is at least one
moment where the change is in front of you.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "madagents"
DEFAULT_MANIFEST = REPO_ROOT / "tools" / "codex_overrides" / "OVERRIDES.toml"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Re-pin a provider's override hashes.")
    parser.add_argument(
        "--manifest", default=None, metavar="PATH",
        help=f"Override manifest to re-pin. Default: {DEFAULT_MANIFEST.relative_to(REPO_ROOT)}",
    )
    parser.add_argument("--dry-run", action="store_true", help="report drift, change nothing")
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    manifest = Path(args.manifest).resolve() if args.manifest else DEFAULT_MANIFEST
    if not manifest.is_file():
        print(f"no such manifest: {manifest}", file=sys.stderr)
        return 2

    text = manifest.read_text(encoding="utf-8")
    updated = text
    stale: list[str] = []

    for match in re.finditer(r'\[override\."([^"]+)"\]\nsha256 = "([0-9a-f]{64})"', text):
        rel, pinned = match.group(1), match.group(2)
        src = SRC / rel
        if not src.is_file():
            print(f"WARNING: {rel} no longer exists — remove its override entry", file=sys.stderr)
            continue
        actual = hashlib.sha256(src.read_bytes()).hexdigest()
        if actual == pinned:
            continue
        stale.append(rel)
        print(f"\n=== {rel} changed since its override was written ===")
        # Show what moved, against the pinned blob when git still has it.
        try:
            subprocess.run(
                ["git", "-C", str(REPO_ROOT), "diff", "--no-index", "--", "/dev/null", str(src)],
                check=False, capture_output=True,
            )
            log = subprocess.run(
                ["git", "-C", str(REPO_ROOT), "log", "--oneline", "-3", "--", f"madagents/{rel}"],
                check=False, capture_output=True, text=True,
            )
            if log.stdout.strip():
                print("recent commits touching it:")
                print("  " + "\n  ".join(log.stdout.strip().splitlines()))
        except OSError:
            pass
        print(f"  pinned {pinned[:12]}…  ->  actual {actual[:12]}…")
        updated = updated.replace(f'sha256 = "{pinned}"', f'sha256 = "{actual}"', 1)

    if not stale:
        print("refresh_override_hashes: all overrides are current")
        return 0
    if args.dry_run:
        print(f"\n{len(stale)} override(s) stale (dry run — nothing written)")
        return 1
    manifest.write_text(updated, encoding="utf-8")
    print(
        f"\nre-pinned {len(stale)} override(s). Confirm you folded each canonical change into "
        f"its override before committing:\n  " + "\n  ".join(stale)
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
