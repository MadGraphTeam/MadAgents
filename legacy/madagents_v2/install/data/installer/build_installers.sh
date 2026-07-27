#!/usr/bin/env bash
# Assemble the installer session directories from the neutral installer source.
#
# The installer's orientation + skills are provider-agnostic; only their placement differs:
#   Claude Code session  -> install/claude_code/.claude/{CLAUDE.md, skills/}
#   Codex session        -> install/codex/{AGENTS.md, .agents/skills/}
#
# Run this whenever install/data/installer/ changes, then commit the regenerated session dirs.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(git -C "$HERE" rev-parse --show-toplevel)/install"
SRC="$ROOT/data/installer"

# ── Claude Code installer session ────────────────────────────────────
CC="$ROOT/claude_code/.claude"
rm -rf "$CC"; mkdir -p "$CC/skills"
cp -a "$SRC/orientation.md" "$CC/CLAUDE.md"
cp -a "$SRC/skills/." "$CC/skills/"
echo "  assembled install/claude_code/.claude/ (CLAUDE.md + $(ls "$CC/skills" | wc -l) skills)"

# ── Codex installer session ──────────────────────────────────────────
CX="$ROOT/codex"
rm -rf "$CX/.agents"; mkdir -p "$CX/.agents/skills"
cp -a "$SRC/orientation.md" "$CX/AGENTS.md"
cp -a "$SRC/skills/." "$CX/.agents/skills/"
echo "  assembled install/codex/ (AGENTS.md + $(ls "$CX/.agents/skills" | wc -l) skills)"

echo "Done. Run codex in install/codex/ or claude in install/claude_code/."
