#!/usr/bin/env bash
# MadAgents — start a session on the agent system installed in this folder.
#
#   ./madagents.sh              start a session
#   ./madagents.sh resume       anything unrecognised is forwarded to codex
#
# What this adds over a bare `codex` here: the lead's instructions — its shipped
# discipline plus the slate it has written for itself. The roster, the skills
# and AGENTS.md are picked up from this directory by Codex itself. The model and
# reasoning effort are yours to pick, as in any other codex session.
#
# First run: Codex asks whether to trust this folder. Answer yes — untrusted, it
# ignores .codex/ entirely and the consultants silently do not exist.
#
# Installed from install/templates/madagents-codex.sh. Everything below is that
# file verbatim except the PROMPT_FILES array, which is substituted at install
# time. `python3 installer.py verify` checks this wrapper against the template.
set -euo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd -- "$HERE"

# @@PROMPT_FILES@@ — the instruction files the lead starts with, in order,
# relative to this folder. One entry per line, quoted.
PROMPT_FILES=(
@@PROMPT_FILES@@
)

SLATE=".madagents/memory/lead/MEMORY.md"
SLATE_HEADER="prompts/lead-slate-header.md"

PROMPT=""
for f in "${PROMPT_FILES[@]}"; do
  [[ -f "$f" ]] || { echo "ERROR: $f is missing — reinstall." >&2; exit 1; }
  if [[ -n "$PROMPT" ]]; then
    PROMPT="$PROMPT

"
  fi
  PROMPT="$PROMPT$(cat -- "$f")"
done

# The lead's slate is concatenated at start-up rather than baked in, because the
# lead rewrites it between sessions — so what it writes is live from the *next*
# session, exactly as auto-memory behaves on Claude Code. Consultants need no
# such step: each one's slate rides inside the role file Codex loads for every
# dispatch of it.
if [[ -s "$SLATE" ]]; then
  [[ -f "$SLATE_HEADER" ]] || {
    echo "ERROR: $SLATE_HEADER is missing — reinstall." >&2
    exit 1
  }
  PROMPT="$PROMPT

$(cat -- "$SLATE_HEADER")

$(cat -- "$SLATE")"
fi

# Additive: Codex splices this into its own developer message rather than
# replacing it (unlike model_instructions_file, which would drop the built-in
# tool and sandbox instructions along with it).
exec codex -c developer_instructions="$PROMPT" "$@"
