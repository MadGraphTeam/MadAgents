#!/usr/bin/env bash
# Run the full evaluation pipeline.
#
# Usage:
#   ./eval/run.sh                                    # default config
#   ./eval/run.sh --config eval/config/pipeline.yaml # custom config
#   ./eval/run.sh --run-dir eval/runs/my_run         # custom run dir
#   ./eval/run.sh --apply-docs                       # apply doc changes after pipeline
#
# Prerequisites:
#   - conda activate MadAgents (or source activate MadAgents)
#   - ./image/examples/create_image.sh
#
# The pipeline runs on the host. Each claude invocation runs inside
# an Apptainer container.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# --- Parse arguments ---
CONFIG="${SCRIPT_DIR}/config/pipeline.yaml"
RUN_DIR=""
APPLY_DOCS=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --config) CONFIG="$2"; shift 2 ;;
    --config=*) CONFIG="${1#*=}"; shift ;;
    --run-dir) RUN_DIR="$2"; shift 2 ;;
    --run-dir=*) RUN_DIR="${1#*=}"; shift ;;
    --apply-docs) APPLY_DOCS=true; shift ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done

# --- Auto-generate run dir if not specified ---
if [[ -z "$RUN_DIR" ]]; then
  STAMP="$(python3 -c "from datetime import datetime, timezone; print(datetime.now(timezone.utc).strftime('%y%m%d_%H%M%S'))")"
  RUN_DIR="${SCRIPT_DIR}/runs/${STAMP}"
fi

# Make paths absolute.
CONFIG="$(realpath "$CONFIG")"
RUN_DIR="$(mkdir -p "$RUN_DIR" && realpath "$RUN_DIR")"

echo "Pipeline"
echo "  Config:     $CONFIG"
echo "  Run dir:    $RUN_DIR"
echo "  Apply docs: $APPLY_DOCS"
echo ""

# --- Load APPTAINER_DIR from config.env ---
if [[ -f "$REPO_ROOT/config.env" ]]; then
  eval "$(grep '^APPTAINER_DIR=' "$REPO_ROOT/config.env")"
  export APPTAINER_DIR
fi

# Unset API keys — Claude Code handles its own authentication.
unset ANTHROPIC_API_KEY OPENAI_API_KEY LLM_API_KEY 2>/dev/null || true

# --- Run pipeline ---
cd "$REPO_ROOT"
# Use conda env's Python directly to avoid conda run buffering.
CONDA_PYTHON="$HOME/.conda/envs/MadAgents/bin/python3"
if [[ ! -x "$CONDA_PYTHON" ]]; then
  CONDA_PYTHON="$(conda run -n MadAgents which python3 2>/dev/null)"
fi

PYTHONPATH="$REPO_ROOT/src" PYTHONUNBUFFERED=1 "$CONDA_PYTHON" -u -c "
import asyncio
import sys
from pathlib import Path
from eval.pipeline import Pipeline, PipelineConfig

config = PipelineConfig.from_yaml(Path('$CONFIG'))
pipeline = Pipeline(config, Path('$REPO_ROOT'), Path('$RUN_DIR'))
asyncio.run(pipeline.run())
"

# --- Apply docs if requested ---
if [[ "$APPLY_DOCS" == "true" ]]; then
  echo ""
  "$SCRIPT_DIR/apply_docs.sh" "$RUN_DIR" --yes
fi
