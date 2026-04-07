#!/usr/bin/env bash
# Diagnose documentation issues from verification errors.
#
# Usage:
#   ./eval/examples/5_diagnose/run.sh                    # diagnose with sonnet
#   ./eval/examples/5_diagnose/run.sh --model haiku       # diagnose with haiku
#
# Prerequisites:
#   ./image/examples/create_image.sh                # build the clean image
#   ./eval/examples/2_answer/run.sh                      # run the answer phase
#   ./eval/examples/3_verify/run.sh                      # run the verify phase
#
# Options:
#   --model MODEL    Model for the diagnoser (default: sonnet)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/container.sh"

VERIFY_DIR="${REPO_ROOT}/eval/examples/3_verify"
ANSWER_DIR="${REPO_ROOT}/eval/examples/2_answer"
GRADE_DIR="${REPO_ROOT}/eval/examples/4_grade"
SIF_PATH="${REPO_ROOT}/image/examples/clean/image.sif"

# --- Check prerequisites ---
if [[ ! -f "$SIF_PATH" ]]; then
  echo "ERROR: Container image not found: $SIF_PATH" >&2
  echo "Build it first:  ./image/examples/create_image.sh" >&2
  exit 1
fi

if [[ ! -f "$ANSWER_DIR/output/results.json" ]]; then
  echo "ERROR: Answer results not found." >&2
  echo "Run the answer phase first:  ./eval/examples/2_answer/run.sh" >&2
  exit 1
fi

if [[ ! -f "$VERIFY_DIR/output/verification/verdicts.json" ]]; then
  echo "ERROR: Verification verdicts not found." >&2
  echo "Run the verify phase first:  ./eval/examples/3_verify/run.sh" >&2
  exit 1
fi

if [[ ! -f "$GRADE_DIR/output/grade/grade.json" ]]; then
  echo "WARNING: Grade not found — diagnose will run without grade context." >&2
  echo "Run the grade phase first:  ./eval/examples/4_grade/run.sh" >&2
fi

# --- Copy output from verify phase ---
OUTPUT_DIR="$SCRIPT_DIR/output"
rm -rf "$OUTPUT_DIR"
rsync -a --exclude='.claude' "$VERIFY_DIR/output/" "$OUTPUT_DIR/"

# --- Copy grade output (from phase 4) ---
if [[ -d "$GRADE_DIR/output/grade" ]]; then
  rsync -a "$GRADE_DIR/output/grade/" "$OUTPUT_DIR/grade/"
fi

# --- Also copy answer transcripts (for reviewer error detection) ---
if [[ -d "$ANSWER_DIR/output/transcripts" ]]; then
  rsync -a "$ANSWER_DIR/output/transcripts/" "$OUTPUT_DIR/transcripts/" 2>/dev/null
fi

# --- Fresh claude config ---
init_claude_config "$SCRIPT_DIR/claude_config"

# --- Cleanup on exit ---
cleanup() {
  if [[ -d "$OUTPUT_DIR" ]] && [[ -z "$(ls -A "$OUTPUT_DIR" 2>/dev/null)" ]]; then
    rmdir "$OUTPUT_DIR" 2>/dev/null || true
  fi
}
trap cleanup EXIT

# --- Run inside container ---
"$APPTAINER_BIN" exec \
  "${CONTAINER_FLAGS[@]}" \
  "${CONTAINER_ENV[@]}" \
  --pwd /output \
  -B "$SCRIPT_DIR/claude_config:/claude_config" \
  -B "$OUTPUT_DIR:/output" \
  "${CONTAINER_BINDS[@]}" \
  -B "$SCRIPT_DIR/diagnose_live.py:/diagnose_live.py:ro" \
  -B "$ANSWER_DIR/output/results.json:/input/results.json:ro" \
  "${CLAUDE_BIND_ARGS[@]}" \
  "$SIF_PATH" \
  python3 /diagnose_live.py "$@"

# --- Done ---
if [[ -f "$OUTPUT_DIR/diagnose/diagnoses.json" ]]; then
  echo ""
  echo "Output: $OUTPUT_DIR/diagnose/diagnoses.json"
fi
