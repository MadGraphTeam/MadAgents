#!/usr/bin/env bash
# Shared container setup for MadAgents examples.
#
# Source this from any run.sh:
#   source "$(dirname "${BASH_SOURCE[0]}")/../lib/container.sh"
#
# After sourcing, the following are available:
#   REPO_ROOT           — absolute path to the repository root
#   APPTAINER_BIN       — path to the apptainer binary
#   CLAUDE_CREDS        — path to .credentials.json on the host
#   CONTAINER_FLAGS     — array of apptainer exec flags
#   CONTAINER_ENV       — array of --env flags
#   CONTAINER_BINDS     — array of -B flags (common mounts)
#   CLAUDE_BIND_ARGS    — array of -B flags for the Claude CLI (may be empty)
#
# The caller should:
#   1. Set SIF_PATH before sourcing (or after, before calling apptainer)
#   2. Append example-specific -B flags to CONTAINER_BINDS
#   3. Run: "$APPTAINER_BIN" exec "${CONTAINER_FLAGS[@]}" "${CONTAINER_ENV[@]}" \
#              "${CONTAINER_BINDS[@]}" "${CLAUDE_BIND_ARGS[@]}" "$SIF_PATH" <cmd>

set -euo pipefail

# ── Resolve repo root ──────────────────────────────────────────────
# Works regardless of where the sourcing script lives.
_lib_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$_lib_dir/../../.." && pwd)"
unset _lib_dir

# ── Load config.env ────────────────────────────────────────────────
if [[ -f "$REPO_ROOT/config.env" ]]; then
  set -a
  # shellcheck source=../../config.env
  source "$REPO_ROOT/config.env"
  set +a
fi

# ── Scrub API keys ─────────────────────────────────────────────────
unset ANTHROPIC_API_KEY OPENAI_API_KEY LLM_API_KEY 2>/dev/null || true

# ── Locate Apptainer ───────────────────────────────────────────────
APPTAINER_BIN=""
if [[ -n "${APPTAINER_DIR-}" ]]; then
  candidate="${APPTAINER_DIR%/}/apptainer"
  [[ -x "$candidate" ]] && APPTAINER_BIN="$candidate"
fi
if [[ -z "$APPTAINER_BIN" ]]; then
  APPTAINER_BIN="$(command -v apptainer || true)"
  if [[ -z "$APPTAINER_BIN" ]]; then
    echo "ERROR: apptainer not found. Set APPTAINER_DIR in config.env." >&2
    exit 1
  fi
fi

# ── Resolve Claude credentials ─────────────────────────────────────
CLAUDE_CFG="${CLAUDE_CONFIG_DIR:-$HOME/.config/.claude}"
CLAUDE_CREDS="$CLAUDE_CFG/.credentials.json"
if [[ ! -f "$CLAUDE_CREDS" ]]; then
  echo "ERROR: Credentials not found: $CLAUDE_CREDS" >&2
  echo "Set CLAUDE_CONFIG_DIR in config.env or run 'claude' to authenticate." >&2
  exit 1
fi

# ── Resolve shared paths ──────────────────────────────────────────
MADGRAPH_DOCS="$REPO_ROOT/src/madagents/software_instructions/madgraph"

# ── Rebuild madgraph-operator agent card ─────────────────────────
python3 "$REPO_ROOT/claude_code/scripts/build_madgraph_operator.py" >/dev/null

# ── Helper: build .claude/ directory for an example ────────────────
# Usage:  build_claude_dir "$SCRIPT_DIR/claude_dir" [--type bare|madagents]
# Delegates to the shared Python builder.
build_example_claude_dir() {
  local dst="$1"; shift
  # chmod first — fakeroot may have created dirs with restrictive perms.
  chmod -R u+rwX "$dst" 2>/dev/null || true
  python3 "$REPO_ROOT/claude_code/scripts/build_claude_dir.py" "$dst" "$@"
}

# ── Helper: create per-example claude config dir ─────────────────
# Usage in run.sh:  init_claude_config "$SCRIPT_DIR/claude_config"
# Creates a fresh config dir with credentials copied from the host.
init_claude_config() {
  local config_dir="$1"
  # chmod first — fakeroot may have created dirs with restrictive perms.
  chmod -R u+rwX "$config_dir" 2>/dev/null || true
  rm -rf "$config_dir"
  mkdir -p "$config_dir"
  cp "$CLAUDE_CREDS" "$config_dir/.credentials.json"
  # Copy other config files if they exist.
  for f in ".claude.json" "settings.json"; do
    [[ -f "$CLAUDE_CFG/$f" ]] && cp "$CLAUDE_CFG/$f" "$config_dir/$f"
  done
}

# ── Locate Claude CLI ──────────────────────────────────────────────
CLAUDE_BIN="$(command -v claude || echo "$HOME/.local/bin/claude")"
CLAUDE_BIND_ARGS=()

if [[ -x "$CLAUDE_BIN" ]]; then
  REAL_CLAUDE="$(realpath "$CLAUDE_BIN")"
  INSTALL_DIR="$(dirname "$(dirname "$REAL_CLAUDE")")"
  if [[ -d "$INSTALL_DIR/versions" ]]; then
    CLAUDE_BIND_ARGS=(-B "$INSTALL_DIR:/opt/claude:ro")
  fi
fi

# ── Build common arrays ───────────────────────────────────────────
CONTAINER_FLAGS=(
  --fakeroot
  --cleanenv
  --writable-tmpfs
  --no-mount home,cwd
)

CONTAINER_ENV=(
  --env "CLAUDE_CONFIG_DIR=/claude_config"
  --env "TERM=xterm-256color"
  --env "LANG=en_US.UTF-8"
  --env "NPM_CONFIG_CACHE=/tmp/.npm"
  --env "PATH=/opt/claude/versions:/root/.local/bin:/usr/local/bin:/usr/bin:/bin"
)

CONTAINER_BINDS=(
  -B "$REPO_ROOT/src:/src:ro"
  -B "$REPO_ROOT/claude_code:/claude_code:ro"
  -B "$MADGRAPH_DOCS:/madgraph_docs:ro"
)
