#!/usr/bin/env bash
# Launch MadAgents (Codex) in this repository.
# Codex auto-loads AGENTS.md and .codex/agents/*.toml from the repo, so no prompt flag is needed.
#
# Usage: ./start_madagents.sh [--env KEY=VALUE ...] [codex args...]
#   --env KEY=VALUE   set an environment variable for Codex (repeatable)
#   other args        forwarded to `codex` (e.g. resume, exec)
# Variables already exported in your shell are inherited as-is.
set -euo pipefail
cd "$(dirname "$0")"

ENV_PAIRS=(); CODEX_ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --env)   ENV_PAIRS+=("$2"); shift 2 ;;
    --env=*) ENV_PAIRS+=("${1#*=}"); shift ;;
    --)      shift; CODEX_ARGS+=("$@"); break ;;
    *)       CODEX_ARGS+=("$1"); shift ;;
  esac
done

exec env ${ENV_PAIRS[@]+"${ENV_PAIRS[@]}"} codex ${CODEX_ARGS[@]+"${CODEX_ARGS[@]}"}
