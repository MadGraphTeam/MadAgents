#!/usr/bin/env bash
# Iterate: diagnose → improve → reeval in one run.
#
# Runs two isolated container invocations:
#   1. Diagnose + improve (sees previous results/verdicts/grade)
#   2. Reeval: answer + verify + grade (clean container — no diagnose/improve
#      output visible, only the improved docs)
#
# Each run does one iteration. By default reads from its own previous
# output. Use --from-7 for the first iteration (reads from 7_reeval).
#
# Usage:
#   ./eval/examples/8_iterate/run.sh --from-7           # first iteration
#   ./eval/examples/8_iterate/run.sh                    # subsequent iterations
#   ./eval/examples/8_iterate/run.sh --model sonnet
#
# Prerequisites:
#   ./image/examples/create_image.sh
#   ./eval/examples/7_reeval/run.sh (for --from-7)
#
# Options:
#   --from-7                 Read input from 7_reeval (first iteration)
#   --model MODEL            Model for main tasks (default: sonnet)
#   --check-model MODEL      Model for cheap checks (default: haiku)
#   --max-improve-rounds N   Max improve rounds (default: 10)
#   --max-turns N            Max answer turns (default: 3)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/container.sh"

SIF_PATH="${REPO_ROOT}/image/examples/clean/image.sif"
ANSWER_DIR="${REPO_ROOT}/eval/examples/2_answer"
GENERATE_DIR="${REPO_ROOT}/eval/examples/1_generate"
VERIFY_DIR="${REPO_ROOT}/eval/examples/3_verify"

# --- Parse --from-7 flag ---
FROM_7=false
PASSTHROUGH_ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --from-7) FROM_7=true; shift ;;
    *) PASSTHROUGH_ARGS+=("$1"); shift ;;
  esac
done

# --- Determine input source ---
if [[ "$FROM_7" == "true" ]]; then
  PREV_RESULTS_DIR="${REPO_ROOT}/eval/examples/7_reeval/output"
  PREV_DOCS="${REPO_ROOT}/eval/examples/6_improve/docs_working"
  echo "Reading from 7_reeval (first iteration)"
else
  if [[ ! -L "$SCRIPT_DIR/latest" ]]; then
    echo "ERROR: No previous iteration found. Run with --from-7 first." >&2
    exit 1
  fi
  PREV_RESULTS_DIR="$SCRIPT_DIR/latest/reeval"
  PREV_DOCS="$SCRIPT_DIR/latest/docs_working"
  echo "Reading from previous iteration ($(readlink "$SCRIPT_DIR/latest"))"
fi

# --- Check prerequisites ---
if [[ ! -f "$SIF_PATH" ]]; then
  echo "ERROR: Container image not found: $SIF_PATH" >&2
  echo "Build it first:  ./image/examples/create_image.sh" >&2
  exit 1
fi

# Find results file.
PREV_RESULTS=""
for candidate in "$PREV_RESULTS_DIR/results.json" "$PREV_RESULTS_DIR/../results.json"; do
  [[ -f "$candidate" ]] && PREV_RESULTS="$(realpath "$candidate")" && break
done
if [[ -z "$PREV_RESULTS" ]]; then
  echo "ERROR: Previous results not found." >&2
  if [[ "$FROM_7" == "true" ]]; then
    echo "Run:  ./eval/examples/7_reeval/run.sh" >&2
  else
    echo "Run with --from-7 first, or run ./eval/examples/7_reeval/run.sh" >&2
  fi
  exit 1
fi

# Find verdicts and grade.
PREV_VERDICTS=""
for candidate in "$PREV_RESULTS_DIR/verification/verdicts.json" "$PREV_RESULTS_DIR/../verification/verdicts.json"; do
  [[ -f "$candidate" ]] && PREV_VERDICTS="$(realpath "$candidate")" && break
done

PREV_GRADE=""
for candidate in "$PREV_RESULTS_DIR/grade/grade.json" "$PREV_RESULTS_DIR/../grade/grade.json"; do
  [[ -f "$candidate" ]] && PREV_GRADE="$(realpath "$candidate")" && break
done

if [[ -z "$PREV_VERDICTS" ]]; then
  echo "ERROR: Previous verdicts not found." >&2
  exit 1
fi

if [[ ! -d "$PREV_DOCS" ]]; then
  echo "ERROR: Previous improved docs not found at $PREV_DOCS" >&2
  exit 1
fi

echo "  Results: $PREV_RESULTS"
echo "  Docs:    $PREV_DOCS"

# --- Determine iteration number ---
ITER_NUM=1
for d in "$SCRIPT_DIR"/iter_*/; do
  [[ -d "$d" ]] || continue
  n="${d%/}"; n="${n##*iter_}"
  (( n >= ITER_NUM )) && ITER_NUM=$(( n + 1 ))
done
echo "Iteration: $ITER_NUM"

# --- Prepare directories ---
ITER_DIR="$SCRIPT_DIR/iter_${ITER_NUM}"
IMPROVE_OUTPUT="$ITER_DIR/improve_output"
REEVAL_OUTPUT="$ITER_DIR/reeval"
WORKSPACE_DIR="$ITER_DIR/workspace"
DOCS_WORKING="$ITER_DIR/docs_working"
rm -rf "$ITER_DIR"
mkdir -p "$IMPROVE_OUTPUT" "$REEVAL_OUTPUT" "$WORKSPACE_DIR" "$DOCS_WORKING"
init_claude_config "$ITER_DIR/claude_config"

# Symlink "latest" for easy access and as input for next iteration.
rm -f "$SCRIPT_DIR/latest"
ln -s "iter_${ITER_NUM}" "$SCRIPT_DIR/latest"

# --- Copy overlay from answer phase ---
OVERLAY_FILE="$ITER_DIR/overlay.img"
if [[ -f "$ANSWER_DIR/overlay.img" ]]; then
  echo "Copying overlay from answer phase..."
  cp --sparse=always "$ANSWER_DIR/overlay.img" "$OVERLAY_FILE"
else
  echo "Creating fresh overlay..."
  "$APPTAINER_BIN" overlay create --fakeroot --sparse --size 4096 "$OVERLAY_FILE"
fi

CONTAINER_FLAGS=(--fakeroot --cleanenv --no-mount home,cwd)

# --- Docs source (copy current best docs for diffing) ---
DOCS_SOURCE="$ITER_DIR/docs_source"
rm -rf "$DOCS_SOURCE"
cp -r "$PREV_DOCS" "$DOCS_SOURCE"

# --- Build local claude_code with agent card from PREVIOUS docs ---
CLAUDE_CODE_LOCAL="$ITER_DIR/claude_code_local"
rm -rf "$CLAUDE_CODE_LOCAL"
cp -r "$REPO_ROOT/src/claude_code" "$CLAUDE_CODE_LOCAL"
cp -r "$REPO_ROOT/claude_code/scripts" "$CLAUDE_CODE_LOCAL/scripts"

HEADER="$REPO_ROOT/claude_code/prompts/madgraph-operator.header.md"
OVERVIEW="$PREV_DOCS/madgraph_overview.md"

if [[ -f "$HEADER" && -f "$OVERVIEW" ]]; then
  echo "Rebuilding madgraph-operator agent card..."
  python3 -c "
import re
from pathlib import Path
header = Path('$HEADER').read_text().rstrip('\n') + '\n'
overview = Path('$OVERVIEW').read_text()
shifted = re.sub(r'^(#+)', r'#\1', overview, flags=re.MULTILINE)
Path('$CLAUDE_CODE_LOCAL/.claude/agents/madgraph-operator.md').write_text(header + '\n' + shifted)
"
fi

# --- Copy previous transcripts for reviewer error detection ---
PREV_TRANSCRIPTS_DIR=""
for candidate in "$PREV_RESULTS_DIR/transcripts" "$PREV_RESULTS_DIR/../transcripts"; do
  [[ -d "$candidate" ]] && PREV_TRANSCRIPTS_DIR="$candidate" && break
done
if [[ -n "$PREV_TRANSCRIPTS_DIR" ]]; then
  mkdir -p "$IMPROVE_OUTPUT/prev_transcripts"
  cp "$PREV_TRANSCRIPTS_DIR"/*.json "$IMPROVE_OUTPUT/prev_transcripts/" 2>/dev/null
fi

# --- Claim database ---
DB_DIR="${VERIFY_DIR}/db"
mkdir -p "$DB_DIR"

# --- Questions file (for reference answers) ---
QUESTIONS_BIND=()
QUESTIONS_FILE="$GENERATE_DIR/output/questions.json"
if [[ -f "$QUESTIONS_FILE" ]]; then
  QUESTIONS_BIND=(-B "$QUESTIONS_FILE:/input/questions_full.json:ro")
fi

# --- Cleanup on exit ---
cleanup() {
  rm -rf "$WORKSPACE_DIR" "$DOCS_SOURCE" "$CLAUDE_CODE_LOCAL"
  rm -f "$OVERLAY_FILE"
}
trap cleanup EXIT

# --- Ensure bind-mount destinations exist in the overlay ---
"$APPTAINER_BIN" exec \
  --fakeroot \
  --overlay "$OVERLAY_FILE" \
  "$SIF_PATH" \
  bash -c 'for d in /workspace /output /madgraph_docs /db /docs_source /docs_current; do
    [ -e "$d" ] || [ -L "$d" ] || mkdir -p "$d"
  done' 2>/dev/null || true


# ══════════════════════════════════════════════════════════════════
#  Phase 1: Diagnose + Improve
# ══════════════════════════════════════════════════════════════════
echo ""
echo "========== Phase 1: Diagnose + Improve =========="

"$APPTAINER_BIN" exec \
  "${CONTAINER_FLAGS[@]}" \
  "${CONTAINER_ENV[@]}" \
  --overlay "$OVERLAY_FILE" \
  --pwd /output \
  -B "$ITER_DIR/claude_config:/claude_config" \
  -B "$IMPROVE_OUTPUT:/output" \
  -B "$REPO_ROOT/src:/src:ro" \
  -B "$CLAUDE_CODE_LOCAL:/src/claude_code:ro" \
  -B "$PREV_DOCS:/madgraph_docs:ro" \
  -B "$WORKSPACE_DIR:/workspace" \
  -B "$DB_DIR:/db" \
  -B "$DOCS_SOURCE:/docs_source:ro" \
  -B "$DOCS_WORKING:/docs_current" \
  -B "$SCRIPT_DIR/iterate_live.py:/iterate_live.py:ro" \
  -B "$PREV_RESULTS:/input/results.json:ro" \
  -B "$PREV_VERDICTS:/input/verdicts.json:ro" \
  ${PREV_GRADE:+-B "$PREV_GRADE:/input/grade.json:ro"} \
  "${QUESTIONS_BIND[@]}" \
  "${CLAUDE_BIND_ARGS[@]}" \
  "$SIF_PATH" \
  python3 /iterate_live.py --phase improve "${PASSTHROUGH_ARGS[@]}"

# --- Check if improvement succeeded ---
IMPROVE_PHASE="$IMPROVE_OUTPUT/improve_phase.json"
if [[ ! -f "$IMPROVE_PHASE" ]]; then
  echo "ERROR: Phase 1 did not produce a summary." >&2
  exit 1
fi

APPROVED=$(python3 -c "import json; print(json.load(open('$IMPROVE_PHASE')).get('approved', False))")
if [[ "$APPROVED" != "True" ]]; then
  echo ""
  echo "No approved improvements -- skipping reeval."
  # Copy phase summary as final summary.
  cp "$IMPROVE_PHASE" "$ITER_DIR/iterate_summary.json"
  exit 0
fi

# --- Merge improve staging ---
IMPROVE_STAGING="$IMPROVE_OUTPUT/improve/staging"
if [[ -d "$IMPROVE_STAGING" ]]; then
  echo ""
  echo "Merging staged claims from improve phase..."
  python3 -c "
import importlib.util
spec = importlib.util.spec_from_file_location('claim_db', '$REPO_ROOT/src/eval/verify/claim_db.py')
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
from pathlib import Path
db = mod.merge_db(Path('$DB_DIR/claim_db.json'), Path('$IMPROVE_STAGING'))
print(f'  Database now has {len(db)} entries.')
"
fi


# ══════════════════════════════════════════════════════════════════
#  Rebuild agent card from IMPROVED docs
# ══════════════════════════════════════════════════════════════════
IMPROVED_OVERVIEW="$DOCS_WORKING/madgraph_overview.md"
if [[ -f "$HEADER" && -f "$IMPROVED_OVERVIEW" ]]; then
  echo ""
  echo "Rebuilding agent card from improved docs..."
  python3 -c "
import re
from pathlib import Path
header = Path('$HEADER').read_text().rstrip('\n') + '\n'
overview = Path('$IMPROVED_OVERVIEW').read_text()
shifted = re.sub(r'^(#+)', r'#\1', overview, flags=re.MULTILINE)
Path('$CLAUDE_CODE_LOCAL/.claude/agents/madgraph-operator.md').write_text(header + '\n' + shifted)
"
fi


# ══════════════════════════════════════════════════════════════════
#  Phase 2: Reeval (clean container — no previous evaluation artifacts)
# ══════════════════════════════════════════════════════════════════
echo ""
echo "========== Phase 2: Reeval (clean container) =========="

"$APPTAINER_BIN" exec \
  "${CONTAINER_FLAGS[@]}" \
  "${CONTAINER_ENV[@]}" \
  --overlay "$OVERLAY_FILE" \
  --pwd /output \
  -B "$ITER_DIR/claude_config:/claude_config" \
  -B "$REEVAL_OUTPUT:/output" \
  -B "$REPO_ROOT/src:/src:ro" \
  -B "$CLAUDE_CODE_LOCAL:/src/claude_code:ro" \
  -B "$DOCS_WORKING:/madgraph_docs:ro" \
  -B "$DB_DIR:/db" \
  -B "$SCRIPT_DIR/iterate_live.py:/iterate_live.py:ro" \
  -B "$PREV_RESULTS:/input/results.json:ro" \
  "${CLAUDE_BIND_ARGS[@]}" \
  "$SIF_PATH" \
  python3 /iterate_live.py --phase reeval "${PASSTHROUGH_ARGS[@]}"

# --- Merge reeval staging ---
REEVAL_STAGING="$REEVAL_OUTPUT/verification/staging"
if [[ -d "$REEVAL_STAGING" ]]; then
  echo ""
  echo "Merging staged claims from reeval phase..."
  python3 -c "
import importlib.util
spec = importlib.util.spec_from_file_location('claim_db', '$REPO_ROOT/src/eval/verify/claim_db.py')
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
from pathlib import Path
db = mod.merge_db(Path('$DB_DIR/claim_db.json'), Path('$REEVAL_STAGING'))
print(f'  Database now has {len(db)} entries.')
"
fi

# --- Compare reeval grade against original (on the host) ---
REEVAL_GRADE="$REEVAL_OUTPUT/grade/grade.json"
if [[ -f "$REEVAL_GRADE" ]]; then
  echo ""
  python3 -c "
import sys; sys.path.insert(0, '$REPO_ROOT/src')
import json
from eval.grade import is_improved

prev_grade = {}
if '$PREV_GRADE':
    try: prev_grade = json.load(open('$PREV_GRADE'))
    except: pass

reeval_grade = json.load(open('$REEVAL_GRADE'))
improved = is_improved(prev_grade, reeval_grade)

improve_info = {}
try: improve_info = json.load(open('$IMPROVE_PHASE'))
except: pass

def fmt(g):
    name = g.get('grade', '?')
    tags = g.get('tags', [])
    return f\"{name} [{', '.join(tags)}]\" if tags else name

summary = {
    'previous_grade': prev_grade.get('grade', '?'),
    'previous_tags': prev_grade.get('tags', []),
    'new_grade': reeval_grade.get('grade', '?'),
    'new_tags': reeval_grade.get('tags', []),
    'improved': improved,
    'findings': improve_info.get('findings', 0),
    'improve_approved': improve_info.get('approved', False),
    'improve_rounds': improve_info.get('improve_rounds', 0),
    'explanation': reeval_grade.get('explanation', ''),
}
json.dump(summary, open('$ITER_DIR/iterate_summary.json', 'w'), indent=2)

print(f'  Previous: {fmt(prev_grade)}')
print(f'  New:      {fmt(reeval_grade)}')
print(f'  Improved: {\"YES\" if improved else \"NO\"}')
"
  echo ""
  echo "Output:  $ITER_DIR/"
  echo "  Phase 1: $IMPROVE_OUTPUT/"
  echo "  Phase 2: $REEVAL_OUTPUT/"
  echo "  Docs:    $DOCS_WORKING/"
fi
