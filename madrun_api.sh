#!/usr/bin/env bash
set -euo pipefail

# Resolve repo root from this script's location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_PATH="${SCRIPT_DIR}/config.env"

# --- Load system vars from config.env ---
# Precedence: caller env > config.env > CLI flags > script defaults
if [[ ! -f "$CONFIG_PATH" ]]; then
  echo "ERROR: config.env not found at $CONFIG_PATH" >&2
  exit 1
fi

# Save any caller-provided overrides before sourcing
declare -A _caller_env
while IFS='=' read -r _key _rest; do
  _key="${_key%%[[:space:]]*}"
  [[ -z "$_key" || "$_key" == \#* ]] && continue
  [[ -n "${!_key+x}" ]] && _caller_env["$_key"]="${!_key}"
done < "$CONFIG_PATH"

set -a
. "$CONFIG_PATH"
set +a

# Restore caller overrides (caller env takes precedence over config.env)
for _key in "${!_caller_env[@]}"; do
  export "$_key=${_caller_env[$_key]}"
done
unset _caller_env _key _rest

# ---------- usage ----------
usage() {
  cat <<'USAGE'
Usage: madrun_api.sh [-- <extra args passed to madrun_main.py>]

All configuration is via config.env (or caller environment variables).
Caller env vars take precedence over config.env; unset vars use defaults.

See config.env.example for available settings.
USAGE
}

# Resolve relative paths against the directory containing config.env (script dir)
resolve_path() {
  local p="$1"
  if [[ -z "${p}" ]]; then
    echo ""
  elif [[ "${p}" = /* ]]; then
    echo "${p}"
  else
    echo "${SCRIPT_DIR}/${p}"
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --) shift; break ;;
    -*) break ;;
    *)  break ;;
  esac
done

# ---------- paths / vars ----------
PROJECT_DIR="${SCRIPT_DIR}"

output_dir="$(resolve_path "${OUTPUT_DIR:-${PROJECT_DIR}/output}")"
run_dir="$(resolve_path "${RUN_DIR:-${PROJECT_DIR}/run_dir}")"
apptainer_cachedir="$(resolve_path "${APPTAINER_CACHEDIR:-${PROJECT_DIR}/.apptainer/cache}")"
apptainer_configdir="$(resolve_path "${APPTAINER_CONFIGDIR:-${PROJECT_DIR}/.apptainer}")"
npm_config_cache="$(resolve_path "${NPM_CONFIG_CACHE:-${PROJECT_DIR}/.npm}")"
frontend_port="${FRONTEND_PORT:-5173}"
backend_port="${BACKEND_PORT:-8000}"

if [[ -z "${output_dir}" ]]; then
  echo "Error: OUTPUT_DIR resolved to empty" >&2
  exit 2
fi
if [[ -z "${run_dir}" ]]; then
  echo "Error: RUN_DIR resolved to empty" >&2
  exit 2
fi
if ! [[ "${frontend_port}" =~ ^[0-9]+$ ]] || (( frontend_port < 1 || frontend_port > 65535 )); then
  echo "Error: FRONTEND_PORT must be an integer in [1, 65535]" >&2
  exit 2
fi
if ! [[ "${backend_port}" =~ ^[0-9]+$ ]] || (( backend_port < 1 || backend_port > 65535 )); then
  echo "Error: BACKEND_PORT must be an integer in [1, 65535]" >&2
  exit 2
fi

RUN_DIR="${run_dir}"
OUTPUT_DIR="${output_dir}"
if [[ -n "${APPTAINER_DIR-}" ]]; then
  APPTAINER_DIR="$(resolve_path "${APPTAINER_DIR}")"
else
  apptainer_bin="$(command -v apptainer || true)"
  if [[ -z "${apptainer_bin}" ]]; then
    echo "ERROR: apptainer not found on PATH. Set APPTAINER_DIR in config.env." >&2
    exit 1
  fi
  APPTAINER_DIR="$(dirname "${apptainer_bin}")"
fi
APPTAINER_CACHEDIR="${apptainer_cachedir}"
APPTAINER_CONFIGDIR="${apptainer_configdir}"
NPM_CONFIG_CACHE="${npm_config_cache}"

mkdir -p -- "${OUTPUT_DIR}"
mkdir -p -- "${RUN_DIR}"
mkdir -p -- "${APPTAINER_CACHEDIR}" "${APPTAINER_CONFIGDIR}" "${NPM_CONFIG_CACHE}"

export APPTAINER_CACHEDIR
export APPTAINER_CONFIGDIR
export NPM_CONFIG_CACHE
export APPTAINERENV_NPM_CONFIG_CACHE="${NPM_CONFIG_CACHE}"

# ---------- lock (prevent simultaneous runs in same clone) ----------
LOCK_FILE="${RUN_DIR}/.madrun.lock"
exec {LOCK_FD}>"${LOCK_FILE}" || { echo "ERROR: cannot open lock file ${LOCK_FILE}" >&2; exit 1; }
if ! flock -n "${LOCK_FD}"; then
  echo "ERROR: madrun is already running for this clone (lock: ${LOCK_FILE})" >&2
  exit 1
fi
printf '%s\n' "$$" 1>&"${LOCK_FD}"

# ---------- port availability ----------
port_in_use() {
  local port="$1"
  if command -v ss >/dev/null 2>&1; then
    ss -ltn 2>/dev/null | awk 'NR>1 {print $4}' | awk -F: '{print $NF}' | grep -Fxq "${port}"
    return $?
  fi
  if command -v lsof >/dev/null 2>&1; then
    lsof -nP -iTCP:"${port}" -sTCP:LISTEN >/dev/null 2>&1
    return $?
  fi
  if command -v python3 >/dev/null 2>&1; then
    python3 - "${port}" <<'PY'
import socket, sys
port = int(sys.argv[1])
s = socket.socket()
try:
    s.bind(("0.0.0.0", port))
except OSError:
    sys.exit(0)  # in use
else:
    sys.exit(1)  # free
finally:
    s.close()
PY
    return $?
  fi
  if command -v python >/dev/null 2>&1; then
    python - "${port}" <<'PY'
import socket, sys
port = int(sys.argv[1])
s = socket.socket()
try:
    s.bind(("0.0.0.0", port))
except OSError:
    sys.exit(0)  # in use
else:
    sys.exit(1)  # free
finally:
    s.close()
PY
    return $?
  fi
  echo "ERROR: cannot check port availability (need ss, lsof, or python)" >&2
  return 2
}

if port_in_use "${frontend_port}"; then
  echo "ERROR: frontend_port ${frontend_port} is already in use" >&2
  exit 1
fi
if port_in_use "${backend_port}"; then
  echo "ERROR: backend_port ${backend_port} is already in use" >&2
  exit 1
fi

LOGDIR="${RUN_DIR}/logs"
mkdir -p "${LOGDIR}"

SRC_DIR="${PROJECT_DIR}/src"
UI_DIR="${SRC_DIR}/madagents/frontend/ui"
MADGRAPH_DOCS_DIR="${SRC_DIR}/madagents/software_instructions/madgraph"

APPTAINER_BIN="${APPTAINER_DIR%/}/apptainer"
if [[ ! -x "${APPTAINER_BIN}" ]]; then
  echo "ERROR: apptainer not found at ${APPTAINER_BIN}. Set --apptainer_dir or APPTAINER_DIR in config.env." >&2
  exit 1
fi

IMAGE="${PROJECT_DIR}/image/madagents.sif"
OVERLAY="${PROJECT_DIR}/image/mad_overlay.img"

MADRUN_LOG="${LOGDIR}/madrun.log"
APPTAINER_LOG="${LOGDIR}/apptainer.log"
LINKS_LOG="${LOGDIR}/madagents_links.txt"
INSTANCE_NAME_FILE="${LOGDIR}/instance_name.txt"
SOCK_PATH="/runs/user_bridge/attach.sock"

DRIVER_PID=""
SESSION_STARTED=false
INSTANCE_NAME=""

list_instances() {
  "${APPTAINER_BIN}" instance list 2>/dev/null | awk 'NR>1 {print $1}'
}

instance_exists() {
  local name="$1"
  list_instances | grep -Fxq "${name}"
}

# ---------- cleanup ----------
cleanup() {
  # Prevent re-entrant cleanup on repeated signals
  trap '' INT TERM HUP
  trap - EXIT

  status=$?

  printf '\nClosing MadAgents ...\n'

  # If we started the driver, stop its whole process group
  if [[ -n "${DRIVER_PID-}" ]]; then
    kill -INT -"${DRIVER_PID}" 2>/dev/null || true
    # Give the driver a few seconds to exit, then move on
    timeout 5 tail --pid="${DRIVER_PID}" -f /dev/null 2>/dev/null || true
  fi

  # Stop the apptainer instance if we started one
  if [[ "${SESSION_STARTED}" == "true" && -n "${INSTANCE_NAME}" ]]; then
    "${APPTAINER_BIN}" instance stop "${INSTANCE_NAME}" 2>/dev/null || true
  fi

  exit "$status"
}

trap cleanup EXIT INT TERM HUP

# ---------- pre-run cleanup ----------
rm -rf -- "${RUN_DIR}/user_bridge" || true

# Clean up overlay artifacts left by claude_code/madrun.sh.
# Claude Code creates /workspace as a directory for bind mounts;
# v1.1 needs it as a symlink for its workspace management.
"${APPTAINER_BIN}" exec \
  --fakeroot \
  --overlay "${OVERLAY}" \
  "${IMAGE}" \
  bash -c '
    for d in /project /prompts; do rmdir "$d" 2>/dev/null || true; done
    if [ -d /workspace ]; then
      if [ -L /workspace ]; then :; else rmdir /workspace 2>/dev/null || true; fi
    fi
  ' 2>/dev/null || true

# ---------- startup message ----------
echo "Starting MadAgents ..."

# ---------- start instance ----------
# TODO: Use
# --overlay "${OVERLAY}" \
# --overlay "${OVERLAY}":/opt \
INSTANCE_BASE="madagents"
for i in $(seq 0 999); do
  if (( i == 0 )); then
    candidate="${INSTANCE_BASE}"
  else
    candidate="${INSTANCE_BASE}-${i}"
  fi

  if "${APPTAINER_BIN}" instance start \
    --fakeroot \
    -B "${SRC_DIR}:/MadAgents/src:ro" \
    -B "${UI_DIR}:/MadAgents/src/madagents/frontend/ui" \
    -B "${MADGRAPH_DOCS_DIR}:/madgraph_docs:ro" \
    -B "${output_dir}:/output" \
    -B "${RUN_DIR}:/runs" \
    --overlay "${OVERLAY}" \
    "${IMAGE}" \
    "${candidate}" \
    >"${APPTAINER_LOG}" 2>&1; then
    SESSION_STARTED=true
    INSTANCE_NAME="${candidate}"
    printf '%s\n' "${INSTANCE_NAME}" > "${INSTANCE_NAME_FILE}"
    break
  fi

  if instance_exists "${candidate}"; then
    continue
  fi

  echo "ERROR: failed to start apptainer instance ${candidate}. See ${APPTAINER_LOG}" >&2
  exit 1
done

if [[ -z "${INSTANCE_NAME}" ]]; then
  echo "ERROR: could not find a free apptainer instance name based on ${INSTANCE_BASE}" >&2
  exit 1
fi

# ---------- start driver ----------
setsid "${APPTAINER_BIN}" exec --pwd /output instance://"${INSTANCE_NAME}" \
  /bin/env PYTHONPATH="/MadAgents/src:${PYTHONPATH:-}" \
  python3 -m madagents.madrun_main \
  --frontend_port "${frontend_port}" \
  --backend_port "${backend_port}" \
  "$@" \
  >"${MADRUN_LOG}" 2>&1 &
DRIVER_PID=$!

# ---------- wait for socket ----------
session_ready=false
for _ in {1..600}; do
  if "${APPTAINER_BIN}" exec instance://"${INSTANCE_NAME}" test -S "${SOCK_PATH}"; then
    session_ready=true
    break
  fi
  sleep 0.1
done

if ! $session_ready; then
  echo "ERROR: timed out waiting for bridge socket ${SOCK_PATH}" >&2
  exit 1
fi

# ---------- print interface links ----------
links_ready=false
for _ in {1..300}; do
  if [[ -s "${LINKS_LOG}" ]]; then
    links_ready=true
    break
  fi
  sleep 0.1
done

if $links_ready; then
  cat "${LINKS_LOG}"
else
  echo "WARN: interface links not available yet at ${LINKS_LOG}" >&2
fi

# ---------- start local madgraph cli ----------
"${APPTAINER_BIN}" exec --pwd /output instance://"${INSTANCE_NAME}" \
  python /MadAgents/src/madagents/cli_bridge/attach_client.py \
    --workdir /runs/user_bridge

# When attach_client exits, script exits; cleanup trap will run.
