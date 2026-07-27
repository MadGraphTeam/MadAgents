#!/usr/bin/env bash
# Regression check: re-render both providers and diff against the committed golden examples.
# Exits non-zero on any drift. Run in CI / before shipping a schema or adapter change.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE="$(git -C "$HERE" rev-parse --show-toplevel)"
EXP="$HERE/expected"
fail=0

chk() {  # <provider> <render.sh>
  local provider="$1" render="$2" out
  out="$(mktemp -d)"
  "$render" "$SOURCE" "$out" bare "<DOCS>"
  rm -rf "$out/madgraph_docs"
  if diff -rq "$EXP/$provider" "$out" >/dev/null 2>&1; then
    printf '  \033[32mOK\033[0m   %s matches golden\n' "$provider"
  else
    printf '  \033[31mDIFF\033[0m %s differs from golden (run regen_expected.sh if intended):\n' "$provider"
    diff -rq "$EXP/$provider" "$out" | sed 's/^/        /'
    fail=1
  fi
  rm -rf "$out"
}

chk claude_code "$SOURCE/install/data/madagents/adapters/claude_code/render.sh"
chk codex       "$SOURCE/install/data/madagents/adapters/codex/render.sh"
[ "$fail" -eq 0 ] && echo "Golden examples up to date." || echo "Golden examples are stale."
exit $fail
