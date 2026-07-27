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
# Precedence: caller env > config.env > script defaults
CONFIG_PATH="${SCRIPT_DIR}/config.env"
if [[ -f "${CONFIG_PATH}" ]]; then
  # Save any caller-provided overrides before sourcing
  declare -A _caller_env
  while IFS='=' read -r _key _rest; do
    _key="${_key%%[[:space:]]*}"
    [[ -z "$_key" || "$_key" == \#* ]] && continue
    [[ -n "${!_key+x}" ]] && _caller_env["$_key"]="${!_key}"
  done < "${CONFIG_PATH}"

  set -a; . "${CONFIG_PATH}"; set +a

  # Restore caller overrides (CLI env takes precedence over config.env)
  for _key in "${!_caller_env[@]}"; do
    export "$_key=${_caller_env[$_key]}"
  done
  unset _caller_env _key _rest
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
IMAGE="${APPTAINER_IMAGE:-image/madagents.sif}"
OVERLAY="${APPTAINER_OVERLAY:-image/mad_overlay.img}"
[[ "${IMAGE}"   = /* ]] || IMAGE="${SCRIPT_DIR}/${IMAGE}"
[[ "${OVERLAY}" = /* ]] || OVERLAY="${SCRIPT_DIR}/${OVERLAY}"

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
  # Lock might be stale: previous run's apptainer daemon inherited the FD and
  # is still holding it even though the script process is gone. Detect that
  # case by checking the recorded PID; if it's dead, kill any process still
  # holding the file (the orphan daemon) and retry once.
  prev_pid="$(head -n1 "${LOCK_FILE}" 2>/dev/null | tr -d '[:space:]')"
  if [[ -n "${prev_pid}" ]] && kill -0 "${prev_pid}" 2>/dev/null; then
    echo "ERROR: madrun is already running (PID ${prev_pid}, lock: ${LOCK_FILE})" >&2
    exit 1
  fi
  echo "WARNING: stale madrun lock detected — killing leftover holders ..." >&2
  fuser -k "${LOCK_FILE}" 2>/dev/null || true
  sleep 1
  if ! flock -n "${LOCK_FD}"; then
    echo "ERROR: could not acquire madrun lock after cleanup (lock: ${LOCK_FILE})" >&2
    exit 1
  fi
fi
# Truncate any stale PID from a previous run before recording our own.
: >"${LOCK_FILE}"
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

# Only pass --session-id if the user isn't resuming/continuing an existing session.
SESSION_ID_ARGS=(--session-id "${SESSION_UUID}")
for arg in "$@"; do
  if [[ "$arg" == "--resume" || "$arg" == "--continue" ]]; then
    SESSION_ID_ARGS=()
    break
  fi
done

# ── Build generated agent cards ───────────────────────────────────────
python3 "${CLAUDE_CODE_DIR}/scripts/build_madgraph_operator.py" >/dev/null

# ── Feature flags (opt-in) ────────────────────────────────────────────
ENABLE_VERIFY="${ENABLE_VERIFY:-0}"
ENABLE_DOC_EDITING="${ENABLE_DOC_EDITING:-0}"

# Doc editing implies verify.
[[ "${ENABLE_DOC_EDITING}" == "1" ]] && ENABLE_VERIFY="1"

# ── Build staging .claude/ directory ─────────────────────────────────
STAGING_CLAUDE="${WORKDIR}/.claude"
BUILD_FLAGS=""
[[ "${ENABLE_VERIFY}" == "1" ]] && BUILD_FLAGS="${BUILD_FLAGS} --verify"
[[ "${ENABLE_DOC_EDITING}" == "1" ]] && BUILD_FLAGS="${BUILD_FLAGS} --doc-editing"
python3 "${CLAUDE_CODE_DIR}/scripts/build_claude_dir.py" "${STAGING_CLAUDE}" --type madagents --symlink ${BUILD_FLAGS} >/dev/null

# ── Start MCP docs server on the host ────────────────────────────────
MCP_PORT="${MCP_PORT:-8089}"
MCP_PID=""
GENERATED_MCP_JSON="${WORKDIR}/.mcp.json"
if [[ "${ENABLE_DOC_EDITING}" == "1" ]]; then
  if [[ ! -f "${CLAUDE_CODE_DIR}/mcp/docs_server.py" ]]; then
    echo "ERROR: ENABLE_DOC_EDITING=1 but ${CLAUDE_CODE_DIR}/mcp/docs_server.py not found." >&2
    exit 1
  fi
  if ! [[ "${MCP_PORT}" =~ ^[0-9]+$ ]] || (( MCP_PORT < 1 || MCP_PORT > 65535 )); then
    echo "ERROR: MCP_PORT must be an integer in [1, 65535] (got: ${MCP_PORT})" >&2
    exit 1
  fi
  cat > "${GENERATED_MCP_JSON}" <<EOF
{
  "mcpServers": {
    "madgraph-docs": {
      "type": "http",
      "url": "http://127.0.0.1:${MCP_PORT}/mcp/"
    }
  }
}
EOF
  MCP_LOG="${WORKDIR}/logs/mcp_docs_server.log"
  DOCS_DIR="${SCRIPT_DIR}/src/madagents/software_instructions/madgraph" \
  OVERVIEW_FILE="${SCRIPT_DIR}/src/madagents/software_instructions/madgraph.md" \
  AGENT_HEADER="${CLAUDE_CODE_DIR}/prompts/madgraph-operator.header.md" \
  PATH_MAP="{\"\/workspace\":\"${WORKDIR}/workspace\",\"\/output\":\"${OUTPUT_DIR}\"}" \
  CLAUDE_CONFIG_DIR="${CLAUDE_CONFIG_DIR}" \
  SESSION_ID="${SESSION_UUID}" \
  MCP_PORT="${MCP_PORT}" \
  python3 "${CLAUDE_CODE_DIR}/mcp/docs_server.py" >"${MCP_LOG}" 2>&1 &
  MCP_PID=$!

  # Wait until the MCP server is actually listening on ${MCP_PORT}, or fail.
  # Polls every 100ms for up to 10s.  If the process dies during the wait
  # (e.g. port collision, missing dependency), fail immediately and dump log.
  mcp_ready=false
  for _ in $(seq 1 100); do
    if ! kill -0 "${MCP_PID}" 2>/dev/null; then
      echo "ERROR: MCP docs server died during startup. Log (${MCP_LOG}):" >&2
      cat "${MCP_LOG}" >&2
      exit 1
    fi
    if (exec 3<>"/dev/tcp/127.0.0.1/${MCP_PORT}") 2>/dev/null; then
      exec 3<&- 3>&-
      mcp_ready=true
      break
    fi
    sleep 0.1
  done
  if ! $mcp_ready; then
    echo "ERROR: MCP docs server did not start listening on 127.0.0.1:${MCP_PORT} within 10s. Log (${MCP_LOG}):" >&2
    cat "${MCP_LOG}" >&2
    kill "${MCP_PID}" 2>/dev/null || true
    exit 1
  fi
fi

# Ensure host-side directories exist for bind mounts.
mkdir -p "${CLAUDE_CONFIG_DIR}" "${OUTPUT_DIR}" "${OUTPUT_DIR}/.claude"

# Remove stale .mcp.json from output/ — it's only needed when doc editing
# is enabled (bind-mounted over by CLAUDE_BIND_ARGS).
rm -f "${OUTPUT_DIR}/.mcp.json"

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
  # Try graceful instance stop first (force-kill so stop never blocks waiting for SIGTERM).
  for name in $("${APPTAINER_BIN}" instance list 2>/dev/null | awk 'NR>1 {print $1}' | grep '^madagents-cc' || true); do
    "${APPTAINER_BIN}" instance stop -F "${name}" 2>/dev/null || true
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

# Remove any orphan instance state files left by a SIGKILLed run. Without this,
# `instance start` would pick a non-default name (madagents-cc-1, -2, ...) to
# dodge the stale entry, and the stop trap on the next run wouldn't find it.
ORPHAN_STATE_DIR="${APPTAINER_CONFIGDIR:-${HOME}/.apptainer}/instances/app/$(hostname -s)/$(id -un)"
if [[ -d "${ORPHAN_STATE_DIR}" ]]; then
  for inst_dir in "${ORPHAN_STATE_DIR}"/madagents-cc*; do
    [[ -d "${inst_dir}" ]] || continue
    inst_pid_file="${inst_dir}/$(basename "${inst_dir}").json"
    [[ -f "${inst_pid_file}" ]] || continue
    inst_pid="$(python3 -c "import json,sys;print(json.load(open('${inst_pid_file}')).get('pid',''))" 2>/dev/null)"
    if [[ -z "${inst_pid}" ]] || ! kill -0 "${inst_pid}" 2>/dev/null; then
      rm -rf "${inst_dir}"
    fi
  done
fi

# ── Clean up overlay conflicts from v1.1 ──────────────────────────────
# v1.1 uses /workspace as a symlink; Claude Code needs it as a directory
# for bind mounts.  Remove stale symlinks so the overlay prep can create
# proper directories. No --fakeroot: the overlay is created in no-fakeroot
# mode (see image/create_image.sh) so the user owns the upper dir.
"${APPTAINER_BIN}" exec \
  --overlay "${OVERLAY}" \
  "${IMAGE}" \
  bash -c '
    if [ -L /workspace ]; then rm /workspace; fi
  ' 2>/dev/null || true

# ── Ensure bind-mount destinations exist inside the container ────────
# The SIF image may not contain /workspace, /output, etc.  Create them
# in the persistent overlay so that instance start can mount onto them.
OVERLAY_DIRS="/workspace /output /madgraph_docs /opt/claude /opt/.config/.claude"

"${APPTAINER_BIN}" exec \
  --overlay "${OVERLAY}" \
  "${IMAGE}" \
  bash -c "for d in ${OVERLAY_DIRS}; do
    [ -e \"\$d\" ] || [ -L \"\$d\" ] || mkdir -p \"\$d\"
  done" 2>/dev/null

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

  # Stop MCP docs server.
  if [[ -n "${MCP_PID}" ]]; then
    kill "${MCP_PID}" 2>/dev/null || true
    echo "Stopped MCP docs server (PID ${MCP_PID})"
  fi

  if [[ "${SESSION_STARTED}" == "true" && -n "${INSTANCE_NAME}" ]]; then
    "${APPTAINER_BIN}" instance stop -F "${INSTANCE_NAME}" 2>/dev/null || true
    # Verify; if stop was ignored (e.g. signal swallowed by fakeroot wrapper),
    # SIGKILL the daemon PID directly from the state file.
    inst_state="${APPTAINER_CONFIGDIR:-${HOME}/.apptainer}/instances/app/$(hostname -s)/$(id -un)/${INSTANCE_NAME}/${INSTANCE_NAME}.json"
    if [[ -f "${inst_state}" ]]; then
      inst_pid="$(python3 -c "import json; d=json.load(open('${inst_state}')); print(d.get('ppid') or d.get('pid') or '')" 2>/dev/null)"
      if [[ -n "${inst_pid}" ]] && kill -0 "${inst_pid}" 2>/dev/null; then
        kill -KILL "${inst_pid}" 2>/dev/null || true
      fi
      rm -rf "$(dirname "${inst_state}")"
    fi
  fi

  # Remove Claude Code-specific directories from the overlay so they
  # don't conflict with v1.1's workspace management.
  timeout 10 "${APPTAINER_BIN}" exec \
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
if [[ "${ENABLE_DOC_EDITING}" == "1" ]]; then
  CLAUDE_BIND_ARGS+=(-B "${GENERATED_MCP_JSON}:/output/.mcp.json:ro")
fi

# ── Start Apptainer instance ────────────────────────────────────────
INSTANCE_BASE="madagents-cc"
for i in $(seq 0 99); do
  if (( i == 0 )); then
    candidate="${INSTANCE_BASE}"
  else
    candidate="${INSTANCE_BASE}-${i}"
  fi

  # Run in a subshell that closes LOCK_FD; otherwise the daemonized apptainer
  # instance inherits the lock FD and holds .madrun.lock forever, blocking
  # every subsequent run until the daemon is killed manually.
  #
  # Intentionally no --fakeroot: the LD_PRELOAD/libfakeroot path used in the
  # absence of /etc/subuid entries deadlocks claude 2.1.x at startup. With
  # a no-fakeroot overlay (see image/create_image.sh) the user can still
  # write to /opt, /usr/local, etc. inside the container and have those
  # writes persist in the overlay. The user is uid 1253 inside, which is
  # fine for pip/npm/file installs; the rare ops that strictly require
  # uid 0 (apt) should be done in a separate "apptainer exec --fakeroot
  # --overlay" maintenance shell outside madrun_code.sh.
  if (
    eval "exec ${LOCK_FD}>&-"
    "${APPTAINER_BIN}" instance start \
      --cleanenv \
      --env "CLAUDE_CONFIG_DIR=/opt/.config/.claude" \
      --env "TERM=${TERM:-xterm-256color}" \
      --env "LANG=${LANG:-C.UTF-8}" \
      -B "${CLAUDE_CONFIG_DIR}:/opt/.config/.claude" \
      -B "${OUTPUT_DIR}:/output" \
      -B "${STAGING_CLAUDE}:/output/.claude" \
      -B "${WORKDIR}/workspace:/workspace" \
      -B "${MADGRAPH_DOCS}:/madgraph_docs:ro" \
      ${CLAUDE_BIND_ARGS[@]+"${CLAUDE_BIND_ARGS[@]}"} \
      --overlay "${OVERLAY}" \
      "${IMAGE}" \
      "${candidate}"
  ) >"${APPTAINER_LOG}" 2>&1; then
    SESSION_STARTED=true
    INSTANCE_NAME="${candidate}"
    printf '%s\n' "${INSTANCE_NAME}" > "${WORKDIR}/logs/instance_name.txt"
    echo "Apptainer instance: ${INSTANCE_NAME}"
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

# ── Verify tmux inside the container (required by doc-editing agent teams) ──
if [[ "${ENABLE_DOC_EDITING}" == "1" ]]; then
  if ! "${APPTAINER_BIN}" exec "instance://${INSTANCE_NAME}" \
       bash -c 'command -v tmux >/dev/null 2>&1'; then
    echo "ERROR: ENABLE_DOC_EDITING=1 requires tmux inside the container, but it was not found." >&2
    echo "       The current image was built without tmux. Rebuild with:" >&2
    echo "         ./image/create_image.sh --type preinstall   # or --type clean" >&2
    echo "       (the latest madagents_*.def installs tmux)." >&2
    exit 1
  fi
fi

# ── Run Claude Code inside the instance ──────────────────────────────
# Claude Code sees the user's UID (1253) inside the container — not 0.
# This is intentional: the host-bind-mounted claude binary (Bun) deadlocks
# under apptainer's LD_PRELOAD/libfakeroot path. Permissions are made
# fully permissive via settings.local.json instead of
# --dangerously-skip-permissions (which requires UID 0 and is also blocked
# by the no-fakeroot setup).
CLAUDE_ENV_ARGS=()
CLAUDE_EXTRA_ARGS=()
if [[ "${ENABLE_DOC_EDITING}" == "1" ]]; then
  # Must be a real process env var (settings.local.json env only reaches subprocesses).
  CLAUDE_ENV_ARGS+=(--env "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1")
  # Agent teams launch teammates in tmux panes; both must be set together.
  CLAUDE_EXTRA_ARGS+=(--teammate-mode tmux)
fi
"${APPTAINER_BIN}" exec \
  --cleanenv \
  --env "CLAUDE_CONFIG_DIR=/opt/.config/.claude" \
  --env "TERM=${TERM:-xterm-256color}" \
  --env "LANG=${LANG:-C.UTF-8}" \
  ${CLAUDE_ENV_ARGS[@]+"${CLAUDE_ENV_ARGS[@]}"} \
  --pwd /output \
  "instance://${INSTANCE_NAME}" \
  bash -c 'export PATH="/root/.local/bin:${PATH}"; exec "$@"' _ "${CLAUDE_CONTAINER_BIN}" \
  --append-system-prompt "$(cat "${CLAUDE_CODE_DIR}/prompts/system-prompt-append.md")" \
  ${CLAUDE_EXTRA_ARGS[@]+"${CLAUDE_EXTRA_ARGS[@]}"} \
  ${SESSION_ID_ARGS[@]+"${SESSION_ID_ARGS[@]}"} "$@"

# When Claude Code exits, the script exits and the cleanup trap stops the instance.
