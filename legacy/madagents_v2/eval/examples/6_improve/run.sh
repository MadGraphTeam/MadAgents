#!/usr/bin/env bash
# Apply and verify documentation improvements.
#
# Usage:
#   ./eval/examples/6_improve/run.sh                        # default (sonnet + haiku)
#   ./eval/examples/6_improve/run.sh --model sonnet --max-rounds 5
#
# Prerequisites:
#   ./image/examples/create_image.sh                   # build the clean image
#   ./eval/examples/2_answer/run.sh                         # answer phase
#   ./eval/examples/3_verify/run.sh                         # verify phase
#   ./eval/examples/5_diagnose/run.sh                       # diagnose phase
#
# Options:
#   --model MODEL        Model for improver and fact verifier (default: sonnet)
#   --check-model MODEL  Model for style/quality checks (default: haiku)
#   --max-rounds N       Maximum revision rounds (default: 10)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/container.sh"

DIAGNOSE_DIR="${REPO_ROOT}/eval/examples/5_diagnose"
VERIFY_DIR="${REPO_ROOT}/eval/examples/3_verify"
ANSWER_DIR="${REPO_ROOT}/eval/examples/2_answer"
GENERATE_DIR="${REPO_ROOT}/eval/examples/1_generate"
SIF_PATH="${REPO_ROOT}/image/examples/clean/image.sif"

# --- Check prerequisites ---
if [[ ! -f "$SIF_PATH" ]]; then
  echo "ERROR: Container image not found: $SIF_PATH" >&2
  echo "Build it first:  ./image/examples/create_image.sh" >&2
  exit 1
fi

if [[ ! -f "$DIAGNOSE_DIR/output/diagnose/diagnoses.json" ]]; then
  echo "ERROR: Diagnoses not found." >&2
  echo "Run the diagnose phase first:  ./eval/examples/5_diagnose/run.sh" >&2
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

# Replace --writable-tmpfs with --overlay.
CONTAINER_FLAGS=(--fakeroot --cleanenv --no-mount home,cwd)

# --- Copy output from diagnose phase ---
OUTPUT_DIR="$SCRIPT_DIR/output"
rm -rf "$OUTPUT_DIR"
rsync -a --exclude='.claude' "$DIAGNOSE_DIR/output/" "$OUTPUT_DIR/"

# --- Fresh workspace, claude config ---
WORKSPACE_DIR="$SCRIPT_DIR/workspace"
DOCS_WORKING="$SCRIPT_DIR/docs_working"
rm -rf "$WORKSPACE_DIR" "$DOCS_WORKING"
mkdir -p "$WORKSPACE_DIR" "$DOCS_WORKING"
init_claude_config "$SCRIPT_DIR/claude_config"

# --- Prepare docs source (madgraph/ dir + madgraph.md overview) ---
DOCS_SOURCE="$SCRIPT_DIR/docs_source"
rm -rf "$DOCS_SOURCE"
cp -r "$REPO_ROOT/src/madagents/software_instructions/madgraph" "$DOCS_SOURCE"
cp "$REPO_ROOT/src/madagents/software_instructions/madgraph.md" "$DOCS_SOURCE/madgraph_overview.md"

# --- Claim database (read-only during run, staging for new claims) ---
DB_DIR="${VERIFY_DIR}/db"
mkdir -p "$DB_DIR"

# --- Cleanup on exit ---
cleanup() {
  rm -rf "$WORKSPACE_DIR" "$DOCS_SOURCE"
  rm -f "$OVERLAY_FILE"
}
trap cleanup EXIT

# --- Ensure bind-mount destinations exist in the overlay ---
"$APPTAINER_BIN" exec \
  --fakeroot \
  --overlay "$OVERLAY_FILE" \
  "$SIF_PATH" \
  bash -c 'for d in /workspace /output /madgraph_docs /db /docs_source /docs_working; do
    [ -e "$d" ] || [ -L "$d" ] || mkdir -p "$d"
  done' 2>/dev/null || true

# --- Mount questions file (for reference answers) if available ---
QUESTIONS_BIND=()
QUESTIONS_FILE="$GENERATE_DIR/output/questions.json"
if [[ -f "$QUESTIONS_FILE" ]]; then
  QUESTIONS_BIND=(-B "$QUESTIONS_FILE:/input/questions.json:ro")
fi

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
  -B "$DB_DIR:/db:ro" \
  -B "$DOCS_SOURCE:/docs_source:ro" \
  -B "$DOCS_WORKING:/docs_working" \
  -B "$SCRIPT_DIR/improve_live.py:/improve_live.py:ro" \
  "${QUESTIONS_BIND[@]}" \
  "${CLAUDE_BIND_ARGS[@]}" \
  "$SIF_PATH" \
  python3 /improve_live.py "$@"

# --- Merge staging files into claim database ---
STAGING_DIR="$OUTPUT_DIR/improve/staging"
if [[ -d "$STAGING_DIR" ]]; then
  echo ""
  echo "Merging staged claims into database..."
  python3 -c "
import importlib.util
spec = importlib.util.spec_from_file_location('claim_db', '$REPO_ROOT/src/eval/verify/claim_db.py')
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
from pathlib import Path
db = mod.merge_db(Path('$DB_DIR/claim_db.json'), Path('$STAGING_DIR'))
print(f'  Database now has {len(db)} entries.')
"
fi

# --- Done ---
if [[ -f "$OUTPUT_DIR/improve/improve_summary.json" ]]; then
  echo ""
  echo "Output: $OUTPUT_DIR/improve/"
  echo "Working docs: $DOCS_WORKING"
fi
