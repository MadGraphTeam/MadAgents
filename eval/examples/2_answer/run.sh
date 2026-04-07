#!/usr/bin/env bash
# Run the answer evaluation loop using MadAgents inside a container.
#
# Usage:
#   ./eval/examples/2_answer/run.sh                                    # answer question 0
#   ./eval/examples/2_answer/run.sh --index 1                          # answer question 1
#   ./eval/examples/2_answer/run.sh --questions path/to/questions.json  # custom input
#   ./eval/examples/2_answer/run.sh --model haiku --max-turns 2
#
# Prerequisites:
#   ./image/examples/create_image.sh            # build the clean image first
#
# Options:
#   --index N, -i N     Question index to answer (default: 0)
#   --questions FILE    Path to questions JSON (default: examples/1_generate/output/questions.json)
#   --model MODEL       Model override for the answerer (e.g. sonnet, haiku)
#   --supervisor-model M    Model for the supervisor (default: haiku)
#   --max-turns N       Max answer→supervise turns per question (default: 3)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/container.sh"

SIF_PATH="${REPO_ROOT}/image/examples/clean/image.sif"

# --- Check image exists ---
if [[ ! -f "$SIF_PATH" ]]; then
  echo "ERROR: Container image not found: $SIF_PATH" >&2
  echo "Build it first:  ./image/examples/create_image.sh" >&2
  exit 1
fi

# --- Create fresh overlay (writable layer for software installs) ---
OVERLAY_FILE="$SCRIPT_DIR/overlay.img"
rm -f "$OVERLAY_FILE"
"$APPTAINER_BIN" overlay create --fakeroot --sparse --size 4096 "$OVERLAY_FILE"

# Replace --writable-tmpfs with --overlay (need persistent writes).
CONTAINER_FLAGS=(--fakeroot --cleanenv --no-mount home,cwd)

# --- Prepare directories and fresh claude config ---
WORKSPACE_DIR="$SCRIPT_DIR/workspace"
chmod -R u+rwX "$SCRIPT_DIR/output" 2>/dev/null || true
rm -rf "$WORKSPACE_DIR" "$SCRIPT_DIR/output"
mkdir -p "$WORKSPACE_DIR" "$SCRIPT_DIR/output"
init_claude_config "$SCRIPT_DIR/claude_config"

# --- Cleanup on exit ---
cleanup() {
  rm -rf "$WORKSPACE_DIR"
  # Keep overlay — the verify phase reuses it.
  # Remove output dir if empty.
  if [[ -d "$SCRIPT_DIR/output" ]] && [[ -z "$(ls -A "$SCRIPT_DIR/output" 2>/dev/null)" ]]; then
    rmdir "$SCRIPT_DIR/output" 2>/dev/null || true
  fi
}
trap cleanup EXIT

# --- Resolve questions file (default: generate output) ---
QUESTIONS_FILE="${REPO_ROOT}/eval/examples/1_generate/output/questions.json"

PASSTHROUGH_ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --questions)
      [[ $# -ge 2 ]] || { echo "ERROR: --questions requires a path" >&2; exit 2; }
      QUESTIONS_FILE="$(realpath "$2")"
      shift 2
      ;;
    --questions=*)
      QUESTIONS_FILE="$(realpath "${1#*=}")"
      shift
      ;;
    *)
      PASSTHROUGH_ARGS+=("$1")
      shift
      ;;
  esac
done

if [[ ! -f "$QUESTIONS_FILE" ]]; then
  echo "ERROR: Questions file not found: $QUESTIONS_FILE" >&2
  echo "Generate questions first:  ./eval/examples/1_generate/run.sh" >&2
  exit 1
fi

# --- Sanitize questions file (strip reference_answers) ---
SANITIZED_QUESTIONS="$WORKSPACE_DIR/questions.json"
python3 -c "
import json; from pathlib import Path
qs = json.loads(Path('$QUESTIONS_FILE').read_text())
for q in qs: q.pop('reference_answer', None)
Path('$SANITIZED_QUESTIONS').write_text(json.dumps(qs, indent=2))
"

# --- Ensure bind-mount destinations exist in the overlay ---
"$APPTAINER_BIN" exec \
  --fakeroot \
  --overlay "$OVERLAY_FILE" \
  "$SIF_PATH" \
  bash -c 'for d in /workspace /output /madgraph_docs; do
    [ -e "$d" ] || [ -L "$d" ] || mkdir -p "$d"
  done' 2>/dev/null || true

# --- Run inside container ---
"$APPTAINER_BIN" exec \
  "${CONTAINER_FLAGS[@]}" \
  "${CONTAINER_ENV[@]}" \
  --overlay "$OVERLAY_FILE" \
  --pwd /output \
  -B "$SCRIPT_DIR/claude_config:/claude_config" \
  -B "$SCRIPT_DIR/output:/output" \
  "${CONTAINER_BINDS[@]}" \
  -B "$WORKSPACE_DIR:/workspace" \
  -B "$SCRIPT_DIR/answer_live.py:/answer_live.py:ro" \
  -B "$SANITIZED_QUESTIONS:/input/questions.json:ro" \
  "${CLAUDE_BIND_ARGS[@]}" \
  "$SIF_PATH" \
  python3 /answer_live.py "${PASSTHROUGH_ARGS[@]}"

# --- Done ---
if [[ -f "$SCRIPT_DIR/output/results.json" ]]; then
  echo ""
  echo "Output: $SCRIPT_DIR/output/results.json"
fi
