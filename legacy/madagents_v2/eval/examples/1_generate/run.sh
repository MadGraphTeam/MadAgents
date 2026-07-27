#!/usr/bin/env bash
# Generate evaluation questions using Claude Code inside a container.
#
# Usage:
#   ./eval/examples/1_generate/run.sh                   # 3 questions, default
#   ./eval/examples/1_generate/run.sh -n 5              # 5 questions
#   ./eval/examples/1_generate/run.sh -n 2 --focus "jet matching and merging"
#   ./eval/examples/1_generate/run.sh --model haiku -n 3
#
# Prerequisites:
#   ./image/examples/create_image.sh            # build the clean image first
#
# Options:
#   -n NUM              Number of questions to generate (default: 3)
#   --focus TEXT         Topic focus for the LLM
#   --requirements TEXT  Additional requirements (e.g. difficulty, question style)
#   --model MODEL        Model override (e.g. sonnet, haiku)
#   --prompts-dir DIR    Custom prompts directory

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/container.sh"

SIF_PATH="${REPO_ROOT}/image/examples/clean/image.sif"

# --- Check image exists ---
if [[ ! -f "$SIF_PATH" ]]; then
  echo "ERROR: Container image not found: $SIF_PATH" >&2
  echo "Build it first:  ./image/examples/create_image.sh" >&2
  exit 1
fi

# --- Clean and create output dir, fresh claude config ---
chmod -R u+rwX "$SCRIPT_DIR/output" 2>/dev/null || true
rm -rf "$SCRIPT_DIR/output"
mkdir -p "$SCRIPT_DIR/output"
init_claude_config "$SCRIPT_DIR/claude_config"

# --- Cleanup on exit ---
cleanup() {
  # Remove output dir if empty (no questions produced).
  if [[ -d "$SCRIPT_DIR/output" ]] && [[ -z "$(ls -A "$SCRIPT_DIR/output" 2>/dev/null)" ]]; then
    rmdir "$SCRIPT_DIR/output" 2>/dev/null || true
  fi
}
trap cleanup EXIT

# --- Run inside container ---
"$APPTAINER_BIN" exec \
  "${CONTAINER_FLAGS[@]}" \
  "${CONTAINER_ENV[@]}" \
  --pwd /output \
  -B "$SCRIPT_DIR/claude_config:/claude_config" \
  -B "$SCRIPT_DIR/output:/output" \
  "${CONTAINER_BINDS[@]}" \
  -B "$SCRIPT_DIR/generate_live.py:/generate_live.py:ro" \
  "${CLAUDE_BIND_ARGS[@]}" \
  "$SIF_PATH" \
  python3 /generate_live.py "$@"

# --- Done ---
if [[ -f "$SCRIPT_DIR/output/questions.json" ]]; then
  echo ""
  echo "Output: $SCRIPT_DIR/output/questions.json"
fi
