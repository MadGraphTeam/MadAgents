#!/usr/bin/env bash
# Regenerate the committed golden example setups for both providers.
#
# These are reference renders of the neutral schema for each adapter, used to (a) show what a
# correct install looks like and (b) regression-check the adapters (see check_expected.sh).
#
# Sanitized on purpose — NO private information:
#   - rendered with the docs path as the literal token "<DOCS>" (no real filesystem paths)
#   - the copied madgraph_docs/ tree is excluded (it is a verbatim copy of
#     src/madagents/software_instructions/madgraph and would just duplicate it)
# Run this whenever the neutral schema or an adapter changes.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE="$(git -C "$HERE" rev-parse --show-toplevel)"
EXP="$HERE/expected"

gen() {  # <provider> <render.sh>
  local provider="$1" render="$2" out
  out="$(mktemp -d)"
  "$render" "$SOURCE" "$out" bare "<DOCS>"
  rm -rf "$out/madgraph_docs"                 # exclude the verbatim docs copy
  rm -rf "$EXP/$provider"; mkdir -p "$EXP/$provider"
  cp -a "$out/." "$EXP/$provider/"
  rm -rf "$out"
  echo "  regenerated expected/$provider ($(find "$EXP/$provider" -type f | wc -l) files)"
}

gen claude_code "$SOURCE/install/data/madagents/adapters/claude_code/render.sh"
gen codex       "$SOURCE/install/data/madagents/adapters/codex/render.sh"
echo "Done. Golden examples are sanitized (DOCS=<DOCS>, docs excluded)."
