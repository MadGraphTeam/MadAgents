#!/usr/bin/env bash
# Claude Code adapter — assemble the neutral MadAgents schema into a `.claude/` payload.
#
# Reads the provider-agnostic schema in install/data/madagents/ and renders the exact set of
# files a Claude Code install needs. Shared by install, build_example, and update (which runs
# it on the schema at the installed commit → merge base, and on the current schema → new).
#
# Usage: render.sh <source-root> <out-dir> <mode> <docs-path> [repo-path] [image-path]
#
# Output layout:
#   <out>/CLAUDE.block.md          MadAgents CLAUDE.md content (spliced into a block on install)
#   <out>/rules/*.md
#   <out>/agents/*.md              incl. the assembled madgraph-operator card
#   <out>/system-prompt-append.md  orchestrator role (passed via --append-system-prompt)
#   <out>/madgraph_docs/...        the curated docs
#   <out>/start_madagents.sh       launcher
set -euo pipefail

SRC="${1:?source-root}"; OUT="${2:?out-dir}"; MODE="${3:?mode}"; DOCS_PATH="${4:?docs-path}"
REPO_PATH="${5:-}"; IMAGE="${6:-}"

SCHEMA="$SRC/install/data/madagents"
DOCS_SRC="$SRC/src/madagents/software_instructions"
ADAPTER="$SCHEMA/adapters/claude_code"
[ -d "$SCHEMA/agents" ] || { echo "render: neutral schema not found in $SRC" >&2; exit 1; }

rm -rf "$OUT"; mkdir -p "$OUT/rules" "$OUT/agents" "$OUT/madgraph_docs"

# Stage the renderable parts (context + rules + agents incl. operator header).
STAGE="$(mktemp -d)"; mkdir -p "$STAGE/rules" "$STAGE/agents"
cp -a "$SCHEMA/context.md" "$STAGE/CLAUDE.md"
cp -a "$SCHEMA/rules/."  "$STAGE/rules/"
cp -a "$SCHEMA/agents/." "$STAGE/agents/"

case "$MODE" in
  bare)
    find "$STAGE" -type f -name '*.md' -print0 | xargs -0 sed -i \
      -e '/<!-- container-only -->/,/<!-- \/container-only -->/d' \
      -e "s|{{DOCS}}|$DOCS_PATH|g" ;;
  container)
    find "$STAGE" -type f -name '*.md' -print0 | xargs -0 sed -i \
      -e '/<!-- container-only -->/d' -e '/<!-- \/container-only -->/d' \
      -e "s|{{DOCS}}|$DOCS_PATH|g" -e "s|{{REPO}}|$REPO_PATH|g" ;;
  *) echo "render: mode must be bare|container (got $MODE)" >&2; exit 2 ;;
esac

# Assemble the madgraph-operator card: rendered header + overview, headings shifted +1.
echo >> "$STAGE/agents/madgraph-operator.md"
sed -E 's/^(#+)/#\1/' "$DOCS_SRC/madgraph.md" >> "$STAGE/agents/madgraph-operator.md"

cp -a "$STAGE/CLAUDE.md" "$OUT/CLAUDE.block.md"
cp -a "$STAGE/rules/."   "$OUT/rules/"
cp -a "$STAGE/agents/."  "$OUT/agents/"
cp -a "$SCHEMA/orchestrator.md" "$OUT/system-prompt-append.md"
cp -a "$DOCS_SRC/madgraph/." "$OUT/madgraph_docs/"
case "$MODE" in
  bare)      cp -a "$ADAPTER/launchers/start_madagents.bare.sh" "$OUT/start_madagents.sh" ;;
  container) sed "s|{{IMAGE}}|${IMAGE}|g" "$ADAPTER/launchers/start_madagents.container.sh" > "$OUT/start_madagents.sh" ;;
esac
chmod +x "$OUT/start_madagents.sh"
rm -rf "$STAGE"
