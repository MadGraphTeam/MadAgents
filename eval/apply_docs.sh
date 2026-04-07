#!/usr/bin/env bash
# Apply improved docs from a pipeline run to the actual docs.
#
# Usage:
#   ./eval/apply_docs.sh eval/runs/250329_120000
#   ./eval/apply_docs.sh eval/runs/250329_120000 --yes  # skip confirmation
#
# Shows the diff and asks for confirmation before overwriting.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <run_dir> [--yes]" >&2
  exit 2
fi

RUN_DIR="$1"
AUTO_YES=false
[[ "${2-}" == "--yes" ]] && AUTO_YES=true

DOCS_WORKING="$RUN_DIR/docs_working"
DOCS_TARGET="$REPO_ROOT/src/madagents/software_instructions/madgraph"
OVERVIEW_TARGET="$REPO_ROOT/src/madagents/software_instructions/madgraph.md"

if [[ ! -d "$DOCS_WORKING" ]]; then
  echo "ERROR: No docs_working/ found in $RUN_DIR" >&2
  echo "Run the pipeline first." >&2
  exit 1
fi

# --- Show diff ---
echo "Diff: $DOCS_TARGET vs $DOCS_WORKING"
echo ""

DIFF="$(diff -ruN "$DOCS_TARGET" "$DOCS_WORKING" --exclude='madgraph_overview.md' || true)"
OVERVIEW_DIFF=""
if [[ -f "$DOCS_WORKING/madgraph_overview.md" && -f "$OVERVIEW_TARGET" ]]; then
  OVERVIEW_DIFF="$(diff -u "$OVERVIEW_TARGET" "$DOCS_WORKING/madgraph_overview.md" || true)"
fi

if [[ -z "$DIFF" && -z "$OVERVIEW_DIFF" ]]; then
  echo "No changes to apply."
  exit 0
fi

if [[ -n "$DIFF" ]]; then
  echo "$DIFF"
fi
if [[ -n "$OVERVIEW_DIFF" ]]; then
  echo ""
  echo "--- Overview (madgraph.md) ---"
  echo "$OVERVIEW_DIFF"
fi

LINES=$(echo "$DIFF$OVERVIEW_DIFF" | wc -l)
echo ""
echo "Total: $LINES diff lines"
echo ""

# --- Confirm ---
if [[ "$AUTO_YES" != "true" ]]; then
  read -p "Apply these changes? [y/N] " confirm
  if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo "Aborted."
    exit 0
  fi
fi

# --- Apply ---
# Copy doc files (exclude the overview which goes to a different location).
rsync -a --exclude='madgraph_overview.md' "$DOCS_WORKING/" "$DOCS_TARGET/"
echo "Applied doc changes to $DOCS_TARGET/"

# Copy overview if it was modified.
if [[ -n "$OVERVIEW_DIFF" ]]; then
  cp "$DOCS_WORKING/madgraph_overview.md" "$OVERVIEW_TARGET"
  echo "Applied overview changes to $OVERVIEW_TARGET"
fi

echo "Done."
