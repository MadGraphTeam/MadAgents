#!/usr/bin/env bash
# Re-evaluate: answer the same question with improved docs, verify, grade.
#
# The container sees only the question text and improved docs — no previous
# grade, verdicts, or other evaluation artifacts.  The comparison against
# the original grade is done on the host after the container exits.
#
# Usage:
#   ./eval/examples/7_reeval/run.sh
#   ./eval/examples/7_reeval/run.sh --model sonnet
#
# Prerequisites:
#   ./image/examples/create_image.sh
#   ./eval/examples/2_answer/run.sh
#   ./eval/examples/3_verify/run.sh
#   ./eval/examples/4_grade/run.sh
#   ./eval/examples/6_improve/run.sh
#
# Options:
#   --model MODEL            Model for answerer and verifier (default: sonnet)
#   --supervisor-model M     Model for supervisor (default: haiku)
#   --extractor-model M      Model for claim extraction (default: haiku)
#   --triage-model M         Model for triage (default: haiku)
#   --remember-model M       Model for remember (default: haiku)
#   --grader-model M         Model for grading (default: haiku)
#   --max-turns N            Max answer turns (default: 3)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/container.sh"

ANSWER_DIR="${REPO_ROOT}/eval/examples/2_answer"
GRADE_DIR="${REPO_ROOT}/eval/examples/4_grade"
VERIFY_DIR="${REPO_ROOT}/eval/examples/3_verify"
IMPROVE_DIR="${REPO_ROOT}/eval/examples/6_improve"
SIF_PATH="${REPO_ROOT}/image/examples/clean/image.sif"

# --- Check prerequisites ---
if [[ ! -f "$SIF_PATH" ]]; then
  echo "ERROR: Container image not found: $SIF_PATH" >&2
  echo "Build it first:  ./image/examples/create_image.sh" >&2
  exit 1
fi

if [[ ! -f "$ANSWER_DIR/output/results.json" ]]; then
  echo "ERROR: Answer results not found." >&2
  echo "Run:  ./eval/examples/2_answer/run.sh" >&2
  exit 1
fi

ORIGINAL_GRADE="$GRADE_DIR/output/grade/grade.json"
if [[ ! -f "$ORIGINAL_GRADE" ]]; then
  echo "ERROR: Original grade not found." >&2
  echo "Run:  ./eval/examples/4_grade/run.sh" >&2
  exit 1
fi

if [[ ! -d "$IMPROVE_DIR/docs_working" ]]; then
  echo "ERROR: Improved docs not found." >&2
  echo "Run:  ./eval/examples/6_improve/run.sh" >&2
  exit 1
fi

# --- Copy overlay from answer phase ---
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

# --- Override MADGRAPH_DOCS to point to improved docs ---
IMPROVED_DOCS="$IMPROVE_DIR/docs_working"

# --- Build local copy of claude_code config with rebuilt agent card ---
CLAUDE_CODE_LOCAL="$SCRIPT_DIR/claude_code_local"
rm -rf "$CLAUDE_CODE_LOCAL"
cp -r "$REPO_ROOT/src/claude_code" "$CLAUDE_CODE_LOCAL"
cp -r "$REPO_ROOT/claude_code/scripts" "$CLAUDE_CODE_LOCAL/scripts"

HEADER="$REPO_ROOT/claude_code/prompts/madgraph-operator.header.md"
OVERVIEW="$IMPROVED_DOCS/madgraph_overview.md"

if [[ -f "$HEADER" && -f "$OVERVIEW" ]]; then
  echo "Rebuilding madgraph-operator agent card with improved overview..."
  python3 -c "
import re
from pathlib import Path
header = Path('$HEADER').read_text().rstrip('\n') + '\n'
overview = Path('$OVERVIEW').read_text()
shifted = re.sub(r'^(#+)', r'#\1', overview, flags=re.MULTILINE)
Path('$CLAUDE_CODE_LOCAL/.claude/agents/madgraph-operator.md').write_text(header + '\n' + shifted)
print('  Done.')
"
fi

# --- Prepare directories ---
OUTPUT_DIR="$SCRIPT_DIR/output"
WORKSPACE_DIR="$SCRIPT_DIR/workspace"
rm -rf "$OUTPUT_DIR" "$WORKSPACE_DIR"
mkdir -p "$OUTPUT_DIR" "$WORKSPACE_DIR"
init_claude_config "$SCRIPT_DIR/claude_config"

# --- Claim database ---
DB_DIR="${VERIFY_DIR}/db"
mkdir -p "$DB_DIR"

# --- Cleanup on exit ---
cleanup() {
  rm -rf "$WORKSPACE_DIR" "$CLAUDE_CODE_LOCAL"
  rm -f "$OVERLAY_FILE"
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

# --- Build container binds (override docs + agent card with improved versions) ---
CONTAINER_BINDS=(
  -B "$REPO_ROOT/src:/src:ro"
  -B "$CLAUDE_CODE_LOCAL:/src/claude_code:ro"
  -B "$IMPROVED_DOCS:/madgraph_docs:ro"
)

# --- Run inside container (no previous grade or verdicts mounted) ---
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
  -B "$SCRIPT_DIR/reeval_live.py:/reeval_live.py:ro" \
  -B "$ANSWER_DIR/output/results.json:/input/results.json:ro" \
  "${CLAUDE_BIND_ARGS[@]}" \
  "$SIF_PATH" \
  python3 /reeval_live.py "$@"

# --- Merge staging files into claim database ---
STAGING_DIR="$OUTPUT_DIR/verification/staging"
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

# --- Compare reeval grade against original (on the host, not in the container) ---
REEVAL_GRADE="$OUTPUT_DIR/grade/grade.json"
if [[ -f "$REEVAL_GRADE" && -f "$ORIGINAL_GRADE" ]]; then
  echo ""
  python3 -c "
import sys; sys.path.insert(0, '$REPO_ROOT/src')
import json
from eval.grade import is_improved

original = json.load(open('$ORIGINAL_GRADE'))
reeval = json.load(open('$REEVAL_GRADE'))
improved = is_improved(original, reeval)

def fmt(g):
    name = g.get('grade', '?')
    tags = g.get('tags', [])
    return f\"{name} [{', '.join(tags)}]\" if tags else name

comparison = {
    'original_grade': original.get('grade', '?'),
    'original_tags': original.get('tags', []),
    'reeval_grade': reeval.get('grade', '?'),
    'reeval_tags': reeval.get('tags', []),
    'improved': improved,
    'reeval_explanation': reeval.get('explanation', ''),
}
json.dump(comparison, open('$OUTPUT_DIR/comparison.json', 'w'), indent=2)

print(f'  Original: {fmt(original)}')
print(f'  Re-eval:  {fmt(reeval)}')
print(f'  Improved: {\"YES\" if improved else \"NO\"}')
"
  echo ""
  echo "Output: $OUTPUT_DIR/"
fi
