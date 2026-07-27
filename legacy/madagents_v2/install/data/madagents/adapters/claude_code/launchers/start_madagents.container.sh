#!/usr/bin/env bash
# Launch MadAgents (Claude Code) for this repository inside an Apptainer container.
# The repository is bind-mounted at its real host path, so paths match inside and out.
#
# Usage: ./start_madagents.sh [--env KEY=VALUE ...] [claude args...]
#   --env KEY=VALUE   set an environment variable for Claude inside the container (repeatable)
#   other args        forwarded to `claude` (e.g. --resume, --continue)
#
# Because the container runs with --cleanenv, host environment variables do NOT leak in.
# Host ANTHROPIC_* and CLAUDE_CODE_* variables are auto-forwarded; anything else must be
# passed with --env (or exported and named there).
#
# Overridable via environment:
#   APPTAINER_IMAGE   path to the .sif image            (default: baked at install)
#   APPTAINER_OVERLAY path to the writable overlay      (default: .madagents/overlay.img)
#   APPTAINER_DIR     directory containing `apptainer`  (default: PATH)
#   CLAUDE_CONFIG_DIR host Claude config/auth dir        (default: ~/.claude)
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAD="${REPO}/.madagents"

APPTAINER_IMAGE="${APPTAINER_IMAGE:-{{IMAGE}}}"
APPTAINER_OVERLAY="${APPTAINER_OVERLAY:-${MAD}/overlay.img}"
DOCS="${MAD}/madgraph_docs"
CLAUDE_HOST_CONFIG="${CLAUDE_CONFIG_DIR:-${HOME}/.claude}"

# ── Parse --env passthrough vs claude args ───────────────────────────
ENV_PAIRS=(); CLAUDE_ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --env)   ENV_PAIRS+=("$2"); shift 2 ;;
    --env=*) ENV_PAIRS+=("${1#*=}"); shift ;;
    --)      shift; CLAUDE_ARGS+=("$@"); break ;;
    *)       CLAUDE_ARGS+=("$1"); shift ;;
  esac
done

# Env to forward into the container: explicit --env pairs, plus host ANTHROPIC_*/CLAUDE_CODE_*.
ENV_FORWARD=()
if ((${#ENV_PAIRS[@]})); then for _p in "${ENV_PAIRS[@]}"; do ENV_FORWARD+=(--env "${_p}"); done; fi
for _k in $(compgen -v 2>/dev/null | grep -E '^(ANTHROPIC_|CLAUDE_CODE_)' || true); do
  [[ "${_k}" == CLAUDE_CONFIG_DIR ]] && continue   # set explicitly to the in-container path
  [[ -n "${!_k+x}" ]] && ENV_FORWARD+=(--env "${_k}=${!_k}")
done

# ── Locate apptainer ─────────────────────────────────────────────────
if [[ -n "${APPTAINER_DIR-}" ]]; then
  APPTAINER_BIN="${APPTAINER_DIR%/}/apptainer"
else
  APPTAINER_BIN="$(command -v apptainer 2>/dev/null || true)"
fi
[[ -x "${APPTAINER_BIN}" ]] || { echo "ERROR: apptainer not found. Set APPTAINER_DIR or add it to PATH." >&2; exit 1; }

# ── Validate image + overlay ─────────────────────────────────────────
[[ -f "${APPTAINER_IMAGE}"   ]] || { echo "ERROR: image not found: ${APPTAINER_IMAGE}" >&2; exit 1; }
[[ -f "${APPTAINER_OVERLAY}" ]] || { echo "ERROR: overlay not found: ${APPTAINER_OVERLAY} (re-run the installer)" >&2; exit 1; }
[[ -d "${DOCS}"              ]] || { echo "ERROR: docs not found: ${DOCS} (re-run the installer)" >&2; exit 1; }
mkdir -p "${CLAUDE_HOST_CONFIG}"

# ── Locate host Claude install (bind in if present) ──────────────────
CLAUDE_BIND_ARGS=()
HOST_CLAUDE_INSTALL=""; HOST_CLAUDE_VERSION=""
CLAUDE_BIN="$(command -v claude 2>/dev/null || true)"
if [[ -n "${CLAUDE_BIN}" ]]; then
  CLAUDE_BIN_REAL="$(readlink -f "${CLAUDE_BIN}")"
  HOST_CLAUDE_VERSION="$(basename "${CLAUDE_BIN_REAL}")"
  candidate_dir="$(dirname "$(dirname "${CLAUDE_BIN_REAL}")")"
  if [[ -d "${candidate_dir}/versions" ]]; then
    HOST_CLAUDE_INSTALL="${candidate_dir}"
    CLAUDE_BIND_ARGS+=(-B "${HOST_CLAUDE_INSTALL}:/opt/claude:ro")
  fi
fi

# ── Instance lifecycle ───────────────────────────────────────────────
INSTANCE="madagents-cc-$$"
cleanup() {
  trap '' INT TERM HUP; trap - EXIT
  "${APPTAINER_BIN}" instance stop -F "${INSTANCE}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM HUP

# Ensure bind-mount destinations exist in the overlay (incl. the repo's real path).
"${APPTAINER_BIN}" exec --overlay "${APPTAINER_OVERLAY}" "${APPTAINER_IMAGE}" \
  bash -c "for d in '${REPO}' /madgraph_docs /opt/.config/.claude /opt/claude; do mkdir -p \"\$d\" 2>/dev/null || true; done" 2>/dev/null || true

"${APPTAINER_BIN}" instance start \
  --cleanenv \
  --env "CLAUDE_CONFIG_DIR=/opt/.config/.claude" \
  --env "TERM=${TERM:-xterm-256color}" \
  --env "LANG=${LANG:-C.UTF-8}" \
  -B "${CLAUDE_HOST_CONFIG}:/opt/.config/.claude" \
  -B "${REPO}:${REPO}" \
  -B "${DOCS}:/madgraph_docs:ro" \
  ${CLAUDE_BIND_ARGS[@]+"${CLAUDE_BIND_ARGS[@]}"} \
  --overlay "${APPTAINER_OVERLAY}" \
  "${APPTAINER_IMAGE}" \
  "${INSTANCE}"

# ── Resolve the claude binary inside the container ───────────────────
if [[ -n "${HOST_CLAUDE_INSTALL}" ]]; then
  CLAUDE_CONTAINER_BIN="/opt/claude/versions/${HOST_CLAUDE_VERSION}"
else
  CLAUDE_CONTAINER_BIN="$("${APPTAINER_BIN}" exec "instance://${INSTANCE}" bash -lc 'command -v claude 2>/dev/null || true')"
  if [[ -z "${CLAUDE_CONTAINER_BIN}" ]]; then
    echo "Claude Code not found in container — installing via npm ..."
    "${APPTAINER_BIN}" exec --cleanenv "instance://${INSTANCE}" npm install -g @anthropic-ai/claude-code >&2
    CLAUDE_CONTAINER_BIN="$("${APPTAINER_BIN}" exec "instance://${INSTANCE}" bash -lc 'command -v claude 2>/dev/null || true')"
    [[ -n "${CLAUDE_CONTAINER_BIN}" ]] || { echo "ERROR: could not install Claude Code in the container." >&2; exit 1; }
  fi
fi

# ── Run Claude Code in the repo (real path == cwd) ───────────────────
"${APPTAINER_BIN}" exec \
  --cleanenv \
  --env "CLAUDE_CONFIG_DIR=/opt/.config/.claude" \
  --env "TERM=${TERM:-xterm-256color}" \
  --env "LANG=${LANG:-C.UTF-8}" \
  ${ENV_FORWARD[@]+"${ENV_FORWARD[@]}"} \
  --pwd "${REPO}" \
  "instance://${INSTANCE}" \
  bash -c 'export PATH="/root/.local/bin:${PATH}"; exec "$@"' _ "${CLAUDE_CONTAINER_BIN}" \
  --append-system-prompt "$(cat "${MAD}/system-prompt-append.md")" \
  ${CLAUDE_ARGS[@]+"${CLAUDE_ARGS[@]}"}
