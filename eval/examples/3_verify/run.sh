#!/usr/bin/env bash
# Verify the answer from the answer phase by extracting and checking claims.
#
# Usage:
#   ./eval/examples/3_verify/run.sh                          # verify latest answer
#   ./eval/examples/3_verify/run.sh --model haiku             # use haiku for verification
#
# Prerequisites:
#   ./image/examples/create_image.sh                  # build the clean image
#   ./eval/examples/2_answer/run.sh                          # run the answer phase first
#
# Options:
#   --reset-db               Delete the claim database before running
#   --model MODEL            Model for the verifier (default: sonnet)
#   --extractor-model MODEL  Model for claim extraction (default: haiku)
#   --triage-model MODEL     Model for triage matching (default: haiku)
#   --remember-model MODEL   Model for remember selection (default: haiku)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/container.sh"

ANSWER_DIR="${REPO_ROOT}/eval/examples/2_answer"
SIF_PATH="${REPO_ROOT}/image/examples/clean/image.sif"

# --- Handle --reset-db ---
if [[ "${1-}" == "--reset-db" ]]; then
  rm -f "$SCRIPT_DIR/db/claim_db.json"
  echo "Claim database reset."
  shift
fi

# --- Check prerequisites ---
if [[ ! -f "$SIF_PATH" ]]; then
  echo "ERROR: Container image not found: $SIF_PATH" >&2
  echo "Build it first:  ./image/examples/create_image.sh" >&2
  exit 1
fi

if [[ ! -f "$ANSWER_DIR/output/results.json" ]]; then
  echo "ERROR: Answer results not found: $ANSWER_DIR/output/results.json" >&2
  echo "Run the answer phase first:  ./eval/examples/2_answer/run.sh" >&2
  exit 1
fi

# --- Copy overlay from answer phase (preserves MadGraph installs) ---
OVERLAY_FILE="$SCRIPT_DIR/overlay.img"
rm -f "$OVERLAY_FILE"
if [[ -f "$ANSWER_DIR/overlay.img" ]]; then
  echo "Copying overlay from answer phase..."
  cp --sparse=always "$ANSWER_DIR/overlay.img" "$OVERLAY_FILE"
else
  echo "No answer overlay found — creating fresh overlay..."
  "$APPTAINER_BIN" overlay create --fakeroot --sparse --size 4096 "$OVERLAY_FILE"
fi

# Replace --writable-tmpfs with --overlay (need persistent writes).
CONTAINER_FLAGS=(--fakeroot --cleanenv --no-mount home,cwd)

# --- Copy output from answer phase (skip .claude — sessions create their own) ---
OUTPUT_DIR="$SCRIPT_DIR/output"
rm -rf "$OUTPUT_DIR"
rsync -a --exclude='.claude' "$ANSWER_DIR/output/" "$OUTPUT_DIR/"

# --- Fresh workspace and claude config ---
WORKSPACE_DIR="$SCRIPT_DIR/workspace"
rm -rf "$WORKSPACE_DIR"
mkdir -p "$WORKSPACE_DIR"
init_claude_config "$SCRIPT_DIR/claude_config"

# --- Persistent claim database ---
DB_DIR="$SCRIPT_DIR/db"
mkdir -p "$DB_DIR"

# --- Cleanup on exit ---
cleanup() {
  rm -rf "$WORKSPACE_DIR"
  rm -f "$OVERLAY_FILE"
  # Keep db/ and output/ — they contain results.
}
trap cleanup EXIT

# --- Ensure bind-mount destinations exist in the overlay ---
"$APPTAINER_BIN" exec \
  --fakeroot \
  --overlay "$OVERLAY_FILE" \
  "$SIF_PATH" \
  bash -c 'for d in /workspace /output /madgraph_docs /db; do
    [ -e "$d" ] || [ -L "$d" ] || mkdir -p "$d"
  done' 2>/dev/null || true

# --- Run inside container ---
"$APPTAINER_BIN" exec \
  "${CONTAINER_FLAGS[@]}" \
  "${CONTAINER_ENV[@]}" \
  --overlay "$OVERLAY_FILE" \
  --pwd /output \
  -B "$SCRIPT_DIR/claude_config:/claude_config" \
  -B "$OUTPUT_DIR:/output" \
  "${CONTAINER_BINDS[@]}" \
  -B "$WORKSPACE_DIR:/workspace" \
  -B "$DB_DIR:/db" \
  -B "$SCRIPT_DIR/verify_live.py:/verify_live.py:ro" \
  -B "$ANSWER_DIR/output/results.json:/input/results.json:ro" \
  "${CLAUDE_BIND_ARGS[@]}" \
  "$SIF_PATH" \
  python3 /verify_live.py "$@"

# --- Merge staging files into claim database ---
STAGING_DIR="$OUTPUT_DIR/verification/staging"
if [[ -d "$STAGING_DIR" ]]; then
  echo ""
  echo "Merging staged claims into database..."
  python3 -c "
import json, importlib.util
spec = importlib.util.spec_from_file_location('claim_db', '$REPO_ROOT/src/eval/verify/claim_db.py')
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
from pathlib import Path
db_path = Path('$DB_DIR/claim_db.json')
before = len(json.load(open(db_path))) if db_path.exists() else 0
db = mod.merge_db(db_path, Path('$STAGING_DIR'))
added = len(db) - before
print(f'  Added {added} new claims (database now has {len(db)} entries).')
"
fi

# --- Done ---
if [[ -d "$OUTPUT_DIR/verification" ]]; then
  echo ""
  echo "Output: $OUTPUT_DIR/verification/"
  for f in "$OUTPUT_DIR/verification/"*.json; do
    [[ -f "$f" ]] && echo "  $(basename "$f")"
  done
fi

if [[ -f "$DB_DIR/claim_db.json" ]]; then
  n=$(python3 -c "import json; print(len(json.load(open('$DB_DIR/claim_db.json'))))" 2>/dev/null || echo "?")
  echo ""
  echo "Claim database: $DB_DIR/claim_db.json ($n entries)"
fi
