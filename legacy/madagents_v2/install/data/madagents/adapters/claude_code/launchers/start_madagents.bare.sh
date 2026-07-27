#!/usr/bin/env bash
# Launch MadAgents (Claude Code) in this repository (bare mode — no container).
#
# Usage: ./start_madagents.sh [--env KEY=VALUE ...] [claude args...]
#   --env KEY=VALUE   set an environment variable for Claude (repeatable)
#   other args        forwarded to `claude` (e.g. --resume, --continue)
# Variables already exported in your shell are inherited as-is.
set -euo pipefail
cd "$(dirname "$0")"

ENV_PAIRS=(); CLAUDE_ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --env)   ENV_PAIRS+=("$2"); shift 2 ;;
    --env=*) ENV_PAIRS+=("${1#*=}"); shift ;;
    --)      shift; CLAUDE_ARGS+=("$@"); break ;;
    *)       CLAUDE_ARGS+=("$1"); shift ;;
  esac
done

exec env ${ENV_PAIRS[@]+"${ENV_PAIRS[@]}"} \
  claude --append-system-prompt "$(cat .madagents/system-prompt-append.md)" \
  ${CLAUDE_ARGS[@]+"${CLAUDE_ARGS[@]}"}
