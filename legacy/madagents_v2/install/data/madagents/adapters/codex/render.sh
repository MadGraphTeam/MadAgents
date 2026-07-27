#!/usr/bin/env bash
# Codex adapter — assemble the neutral MadAgents schema into a Codex payload.
#
# Reads the provider-agnostic schema in install/data/madagents/ and renders the files a Codex
# install needs. Shared by install, build_example, and update (base + new).
#
# Usage: render.sh <source-root> <out-dir> <mode> <docs-path> [repo-path] [image-path]
#
# Output layout:
#   <out>/AGENTS.block.md          MadAgents instructions (context + rules + orchestrator),
#                                  spliced into a block in the target's AGENTS.md on install
#   <out>/agents/*.toml            one Codex subagent per MadAgents agent (incl. madgraph-operator)
#   <out>/config.toml              Codex [agents] orchestration config
#   <out>/madgraph_docs/...        the curated docs
#   <out>/start_madagents.sh       launcher (`codex`)
set -euo pipefail

SRC="${1:?source-root}"; OUT="${2:?out-dir}"; MODE="${3:?mode}"; DOCS_PATH="${4:?docs-path}"
REPO_PATH="${5:-}"

SCHEMA="$SRC/install/data/madagents"
DOCS_SRC="$SRC/src/madagents/software_instructions"
ADAPTER="$SCHEMA/adapters/codex"
[ -d "$SCHEMA/agents" ] || { echo "render: neutral schema not found in $SRC" >&2; exit 1; }

rm -rf "$OUT"; mkdir -p "$OUT/agents" "$OUT/madgraph_docs"

# Stage and render the schema (same transform as the Claude adapter).
STAGE="$(mktemp -d)"; mkdir -p "$STAGE/rules" "$STAGE/agents"
cp -a "$SCHEMA/context.md"      "$STAGE/context.md"
cp -a "$SCHEMA/orchestrator.md" "$STAGE/orchestrator.md"
cp -a "$SCHEMA/rules/."         "$STAGE/rules/"
cp -a "$SCHEMA/agents/."        "$STAGE/agents/"

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

# madgraph-operator: rendered header + overview, headings shifted +1.
echo >> "$STAGE/agents/madgraph-operator.md"
sed -E 's/^(#+)/#\1/' "$DOCS_SRC/madgraph.md" >> "$STAGE/agents/madgraph-operator.md"

# AGENTS.md content = environment + rules + orchestrator role.
{
  cat "$STAGE/context.md"
  printf '\n\n# Rules\n\n'
  cat "$STAGE/rules/correctness.md"
  printf '\n'
  cat "$STAGE/rules/mandatory-reviews.md"
  printf '\n\n# Orchestration\n\n'
  cat "$STAGE/orchestrator.md"
} > "$OUT/AGENTS.block.md"

# Each agent -> a Codex subagent TOML.
for f in "$STAGE"/agents/*.md; do
  n="$(basename "$f" .md)"
  python3 "$ADAPTER/agent_to_toml.py" "$f" > "$OUT/agents/$n.toml"
done

cp -a "$ADAPTER/config.toml" "$OUT/config.toml"
cp -a "$DOCS_SRC/madgraph/." "$OUT/madgraph_docs/"
cp -a "$ADAPTER/launchers/start_madagents.sh" "$OUT/start_madagents.sh"; chmod +x "$OUT/start_madagents.sh"
rm -rf "$STAGE"
