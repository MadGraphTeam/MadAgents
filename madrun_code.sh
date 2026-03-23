#!/usr/bin/env bash
# Launch Claude Code inside a persistent Apptainer instance.
#
# Usage: ./madrun_code.sh [claude-code-args...]
#
# Any extra arguments are forwarded to the `claude` CLI, e.g.:
#   ./madrun_code.sh --resume
#   ./madrun_code.sh --continue

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_CODE_DIR="${SCRIPT_DIR}/claude_code"

# ── Load config ──────────────────────────────────────────────────────
CONFIG_PATH="${SCRIPT_DIR}/config.env"
if [[ -f "${CONFIG_PATH}" ]]; then
  set -a; . "${CONFIG_PATH}"; set +a
fi

# API keys from config.env are for the v1.1 stack; Claude Code handles
# its own authentication.  Unset them so they don't leak into subprocesses.
unset OPENAI_API_KEY 2>/dev/null || true
unset ANTHROPIC_API_KEY 2>/dev/null || true
unset LLM_API_KEY 2>/dev/null || true

# ── Shared directory structure ───────────────────────────────────────
OUTPUT_DIR="${OUTPUT_DIR:-${SCRIPT_DIR}/output}"
RUN_DIR="${RUN_DIR:-${SCRIPT_DIR}/run_dir}"
CLAUDE_CONFIG_DIR="${CLAUDE_CONFIG_DIR:-${CLAUDE_CODE_DIR}/.config/.claude}"
MADGRAPH_DOCS="${SCRIPT_DIR}/src/madagents/software_instructions/madgraph"

# ── Locate apptainer ────────────────────────────────────────────────
if [[ -n "${APPTAINER_DIR-}" ]]; then
  APPTAINER_BIN="${APPTAINER_DIR%/}/apptainer"
else
  APPTAINER_BIN="$(command -v apptainer 2>/dev/null || true)"
fi

if [[ -z "${APPTAINER_BIN}" || ! -x "${APPTAINER_BIN}" ]]; then
  echo "ERROR: apptainer not found. Set APPTAINER_DIR in config.env or add apptainer to PATH." >&2
  exit 1
fi

# ── Validate image and overlay ──────────────────────────────────────
IMAGE="${SCRIPT_DIR}/image/madagents.sif"
OVERLAY="${SCRIPT_DIR}/image/mad_overlay.img"

if [[ ! -f "${IMAGE}" ]]; then
  echo "ERROR: Container image not found at ${IMAGE}." >&2
  echo "       Run image/create_image.sh first." >&2
  exit 1
fi

if [[ ! -f "${OVERLAY}" ]]; then
  echo "ERROR: Overlay image not found at ${OVERLAY}." >&2
  echo "       Run image/create_overlay.sh first." >&2
  exit 1
fi

# ── Lock (shared with madrun_api.sh) ──────────────────────────────────
mkdir -p "${RUN_DIR}"
LOCK_FILE="${RUN_DIR}/.madrun.lock"
exec {LOCK_FD}>"${LOCK_FILE}" || { echo "ERROR: cannot open lock file ${LOCK_FILE}" >&2; exit 1; }
if ! flock -n "${LOCK_FD}"; then
  echo "ERROR: madrun is already running (lock: ${LOCK_FILE})" >&2
  exit 1
fi
printf '%s\n' "$$" 1>&"${LOCK_FD}"

# ── Create workdir (v1.1 layout) ────────────────────────────────────
WORKDIRS_BASE="${RUN_DIR}/workdirs"
mkdir -p "${WORKDIRS_BASE}"

STAMP="$(python3 -c "from datetime import datetime, timezone; print(datetime.now(timezone.utc).strftime('%y%m%d_%H%M%S_%f'))")"
WORKDIR="${WORKDIRS_BASE}/${STAMP}"
SUFFIX=0
while [[ -e "${WORKDIR}" ]]; do
  SUFFIX=$((SUFFIX + 1))
  WORKDIR="${WORKDIRS_BASE}/${STAMP}_${SUFFIX}"
done

mkdir -p "${WORKDIR}/workspace" "${WORKDIR}/logs"

SESSION_UUID="$(python3 -c 'import uuid; print(uuid.uuid4())')"
echo -n "${SESSION_UUID}" > "${WORKDIR}/logs/session_uuid"

# ── Build generated agent cards ───────────────────────────────────────
python3 "${CLAUDE_CODE_DIR}/scripts/build_madgraph_operator.py" >/dev/null

# Ensure host-side directories exist for bind mounts.
mkdir -p "${CLAUDE_CONFIG_DIR}" "${OUTPUT_DIR}" "${OUTPUT_DIR}/.claude"

# ── Locate claude installation on host ──────────────────────────────
CLAUDE_BIN="$(command -v claude 2>/dev/null || true)"
if [[ -z "${CLAUDE_BIN}" || ! -x "${CLAUDE_BIN}" ]]; then
  for candidate in "${HOME}/.local/bin/claude" "/usr/local/bin/claude"; do
    if [[ -x "${candidate}" ]]; then
      CLAUDE_BIN="${candidate}"
      break
    fi
  done
fi

HOST_CLAUDE_INSTALL=""
HOST_CLAUDE_VERSION=""
if [[ -n "${CLAUDE_BIN}" && -x "${CLAUDE_BIN}" ]]; then
  CLAUDE_BIN_REAL="$(readlink -f "${CLAUDE_BIN}")"
  HOST_CLAUDE_VERSION="$(basename "${CLAUDE_BIN_REAL}")"
  candidate_dir="$(dirname "$(dirname "${CLAUDE_BIN_REAL}")")"
  if [[ -d "${candidate_dir}/versions" ]]; then
    HOST_CLAUDE_INSTALL="${candidate_dir}"
  fi
fi

# ── Clean up stale processes holding the overlay ─────────────────────
if fuser "${OVERLAY}" >/dev/null 2>&1; then
  echo "WARNING: overlay is locked by another process — cleaning up stale processes ..."
  # Try graceful instance stop first
  for name in $("${APPTAINER_BIN}" instance list 2>/dev/null | awk 'NR>1 {print $1}' | grep '^madagents-cc' || true); do
    "${APPTAINER_BIN}" instance stop "${name}" 2>/dev/null || true
  done
  sleep 1

  # If still locked, kill holding processes directly
  if fuser "${OVERLAY}" >/dev/null 2>&1; then
    fuser -k "${OVERLAY}" 2>/dev/null || true
    sleep 1
  fi

  if fuser "${OVERLAY}" >/dev/null 2>&1; then
    echo "ERROR: cannot release overlay lock. Check running processes with: fuser ${OVERLAY}" >&2
    exit 1
  fi
  echo "Stale processes cleaned up."
fi

# ── Clean up overlay conflicts from v1.1 ──────────────────────────────
# v1.1 uses /workspace as a symlink; Claude Code needs it as a directory
# for bind mounts.  Remove stale symlinks so the overlay prep can create
# proper directories.
"${APPTAINER_BIN}" exec \
  --fakeroot \
  --overlay "${OVERLAY}" \
  "${IMAGE}" \
  bash -c '
    if [ -L /workspace ]; then rm /workspace; fi
  ' 2>/dev/null || true

# ── Ensure bind-mount destinations exist inside the container ────────
# The SIF image may not contain /workspace, /output, etc.  Create them
# in the persistent overlay so that instance start can mount onto them.
"${APPTAINER_BIN}" exec \
  --fakeroot \
  --overlay "${OVERLAY}" \
  "${IMAGE}" \
  bash -c 'for d in /workspace /output /madgraph_docs /opt/claude /opt/.config/.claude; do
    [ -e "$d" ] || [ -L "$d" ] || mkdir -p "$d"
  done'

# ── Instance state ──────────────────────────────────────────────────
APPTAINER_LOG="${WORKDIR}/logs/apptainer.log"
SESSION_STARTED=false
INSTANCE_NAME=""

list_instances() {
  "${APPTAINER_BIN}" instance list 2>/dev/null | awk 'NR>1 {print $1}'
}

instance_exists() {
  list_instances | grep -Fxq "$1"
}

# ── Cleanup ─────────────────────────────────────────────────────────
cleanup() {
  # Prevent re-entrant cleanup on repeated signals
  trap '' INT TERM HUP
  trap - EXIT

  local status=$?
  printf '\nShutting down ...\n'

  if [[ "${SESSION_STARTED}" == "true" && -n "${INSTANCE_NAME}" ]]; then
    "${APPTAINER_BIN}" instance stop "${INSTANCE_NAME}" 2>/dev/null || true
  fi

  # Remove Claude Code-specific directories from the overlay so they
  # don't conflict with v1.1's workspace management.
  timeout 10 "${APPTAINER_BIN}" exec \
    --fakeroot \
    --overlay "${OVERLAY}" \
    "${IMAGE}" \
    bash -c '
      if [ -d /workspace ]; then
        if [ -L /workspace ]; then :; else rmdir /workspace 2>/dev/null || true; fi
      fi
    ' 2>/dev/null || true

  exit "${status}"
}
trap cleanup EXIT INT TERM HUP

# ── Claude Code bind mount (conditional) ────────────────────────────
CLAUDE_BIND_ARGS=()
if [[ -n "${HOST_CLAUDE_INSTALL}" ]]; then
  CLAUDE_BIND_ARGS+=(-B "${HOST_CLAUDE_INSTALL}:/opt/claude:ro")
fi

# ── Start Apptainer instance ────────────────────────────────────────
INSTANCE_BASE="madagents-cc"
for i in $(seq 0 99); do
  if (( i == 0 )); then
    candidate="${INSTANCE_BASE}"
  else
    candidate="${INSTANCE_BASE}-${i}"
  fi

  if "${APPTAINER_BIN}" instance start \
    --fakeroot \
    --cleanenv \
    --env "CLAUDE_CONFIG_DIR=/opt/.config/.claude" \
    --env "TERM=${TERM:-xterm-256color}" \
    --env "LANG=${LANG:-C.UTF-8}" \
    -B "${CLAUDE_CONFIG_DIR}:/opt/.config/.claude" \
    -B "${OUTPUT_DIR}:/output" \
    -B "${CLAUDE_CODE_DIR}/.claude:/output/.claude" \
    -B "${WORKDIR}/workspace:/workspace" \
    -B "${MADGRAPH_DOCS}:/madgraph_docs:ro" \
    ${CLAUDE_BIND_ARGS[@]+"${CLAUDE_BIND_ARGS[@]}"} \
    --overlay "${OVERLAY}" \
    "${IMAGE}" \
    "${candidate}" \
    >"${APPTAINER_LOG}" 2>&1; then
    SESSION_STARTED=true
    INSTANCE_NAME="${candidate}"
    printf '%s\n' "${INSTANCE_NAME}" > "${WORKDIR}/logs/instance_name.txt"
    break
  fi

  # If the name was taken by another session, try the next one
  if instance_exists "${candidate}"; then
    continue
  fi

  echo "ERROR: failed to start Apptainer instance '${candidate}'. See ${APPTAINER_LOG}" >&2
  exit 1
done

if [[ -z "${INSTANCE_NAME}" ]]; then
  echo "ERROR: could not find a free instance name (tried ${INSTANCE_BASE} through ${INSTANCE_BASE}-99)." >&2
  exit 1
fi

# ── Ensure Claude Code is available ────────────────────────────────
if [[ -n "${HOST_CLAUDE_INSTALL}" ]]; then
  # Host installation bind-mounted — use the versioned binary directly
  CLAUDE_CONTAINER_BIN="/opt/claude/versions/${HOST_CLAUDE_VERSION}"
else
  # No host installation — check overlay for a previous install, or install now
  CLAUDE_CONTAINER_BIN="$("${APPTAINER_BIN}" exec "instance://${INSTANCE_NAME}" \
    bash -c 'command -v claude 2>/dev/null || true')"

  if [[ -z "${CLAUDE_CONTAINER_BIN}" ]]; then
    echo "Claude Code not found on host. Installing inside the container..."
    if ! "${APPTAINER_BIN}" exec \
      --cleanenv \
      "instance://${INSTANCE_NAME}" \
      npm install -g @anthropic-ai/claude-code; then
      echo "ERROR: Failed to install Claude Code inside the container." >&2
      echo "       Install Claude Code on the host first, or ensure npm is available in the container." >&2
      exit 1
    fi
    CLAUDE_CONTAINER_BIN="$("${APPTAINER_BIN}" exec "instance://${INSTANCE_NAME}" \
      bash -c 'command -v claude 2>/dev/null || true')"
    if [[ -z "${CLAUDE_CONTAINER_BIN}" ]]; then
      echo "ERROR: Claude Code binary not found after installation." >&2
      exit 1
    fi
  fi
fi

# ── Run Claude Code inside the instance ──────────────────────────────
# --fakeroot is inherited from the instance, so Claude Code sees UID 0.
# Because of this, --dangerously-skip-permissions cannot be used.
# Permissions are made fully permissive via settings.local.json instead.
"${APPTAINER_BIN}" exec \
  --cleanenv \
  --env "CLAUDE_CONFIG_DIR=/opt/.config/.claude" \
  --env "TERM=${TERM:-xterm-256color}" \
  --env "LANG=${LANG:-C.UTF-8}" \
  --pwd /output \
  "instance://${INSTANCE_NAME}" \
  bash -c 'export PATH="/root/.local/bin:${PATH}"; exec "$@"' _ "${CLAUDE_CONTAINER_BIN}" \
  --append-system-prompt "$(cat "${CLAUDE_CODE_DIR}/prompts/system-prompt-append.md")" \
  --session-id "${SESSION_UUID}" "$@"

# When Claude Code exits, the script exits and the cleanup trap stops the instance.
