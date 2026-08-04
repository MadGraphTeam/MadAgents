#!/usr/bin/env bash
# MadAgents — start a session on the agent system installed in this folder.
#
#   ./madagents.sh              start a session
#   ./madagents.sh --resume     anything unrecognised is forwarded to claude
#
# What this adds over a bare `claude` here: the lead's system prompt. The
# roster, the skills, the learned tier and CLAUDE.md are picked up from this
# directory by Claude Code itself, and the model is yours to pick as in any
# other session.
#
# Installed from install/templates/madagents.sh. Everything below is that file
# verbatim except the two arrays, which are substituted at install time. If you
# are reading this because something is wrong, `python3 installer.py verify`
# checks this wrapper against the template.
set -euo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd -- "$HERE"

# @@PROMPT_FILES@@ — the system-prompt files the lead starts with, in order,
# relative to this folder. One entry per line, quoted.
PROMPT_FILES=(
@@PROMPT_FILES@@
)

# @@DISALLOWED_TOOLS@@ — usually empty. One tool name per line, quoted.
DISALLOWED_TOOLS=(
@@DISALLOWED_TOOLS@@
)

FLAGS=()
for f in "${PROMPT_FILES[@]}"; do
  [[ -f "$f" ]] || { echo "ERROR: $f is missing — reinstall." >&2; exit 1; }
  FLAGS+=(--append-system-prompt "$(cat -- "$f")")
done
if ((${#DISALLOWED_TOOLS[@]})); then
  FLAGS+=(--disallowed-tools "${DISALLOWED_TOOLS[@]}")
fi

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
    settings.write_text(json.dumps(data, indent=2) + "\n")
    print(f"madagents: this folder moved — auto-memory re-pointed at {want}")
PY
fi

exec claude "${FLAGS[@]}" "$@"
