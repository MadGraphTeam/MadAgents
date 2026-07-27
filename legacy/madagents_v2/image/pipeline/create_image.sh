#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
CONFIG_PATH="${REPO_ROOT}/config.env"

# --- Load system vars from config.env ---
if [[ ! -f "$CONFIG_PATH" ]]; then
    echo "ERROR: config.env not found at $CONFIG_PATH" >&2
    exit 1
fi

set -a
# shellcheck disable=SC1091
source "$CONFIG_PATH"
set +a

# --- Locate apptainer binary ---
APPTAINER_BIN=""
if [[ -n "${APPTAINER_DIR-}" ]]; then
    candidate_bin="${APPTAINER_DIR%/}/apptainer"
    if [[ -x "$candidate_bin" ]]; then
        APPTAINER_BIN="${candidate_bin}"
    fi
fi
if [[ -z "${APPTAINER_BIN}" ]]; then
    apptainer_bin="$(command -v apptainer || true)"
    if [[ -z "${apptainer_bin}" ]]; then
        echo "ERROR: apptainer not found. Set APPTAINER_DIR in config.env." >&2
        exit 1
    fi
    APPTAINER_BIN="${apptainer_bin}"
fi

# --- Variant selection ---
VARIANT="${1:-clean}"
DEF_DIR="${SCRIPT_DIR}/${VARIANT}"

if [ ! -d "$DEF_DIR" ]; then
    echo "Error: variant directory '${DEF_DIR}' does not exist." >&2
    echo "Available variants: $(ls -1 "$SCRIPT_DIR" | grep -v '\.sh$' | tr '\n' ' ')" >&2
    exit 1
fi

if [ ! -f "${DEF_DIR}/image.def" ]; then
    echo "Error: '${DEF_DIR}/image.def' not found." >&2
    exit 1
fi

# --- Use scratch for tmp (/tmp is often too small for large images) ---
export APPTAINER_TMPDIR="${REPO_ROOT}/.apptainer_tmp"
mkdir -p "$APPTAINER_TMPDIR"

# --- Build the image ---
cd "$REPO_ROOT"
echo "Building image from ${DEF_DIR}/image.def ..."
"$APPTAINER_BIN" build --fakeroot "${DEF_DIR}/image.sif" "${DEF_DIR}/image.def"
echo "Done: ${DEF_DIR}/image.sif"

# --- Clean up apptainer build artifacts in /tmp ---
echo "Cleaning up build artifacts in /tmp ..."
find /tmp -maxdepth 1 -user "$(id -un)" \( -name 'build-temp-*' -o -name 'bundle-temp-*' -o -name 'overlay-*' \) -exec rm -rf {} +
rm -rf "$APPTAINER_TMPDIR"
"$APPTAINER_BIN" cache clean --force
echo "Cleanup done."
