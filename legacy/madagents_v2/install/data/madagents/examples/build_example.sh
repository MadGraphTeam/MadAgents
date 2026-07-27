#!/usr/bin/env bash
# Reference end-to-end MadAgents install into a demo target, then verify.
#
# Canonical reference for the install-madagents skill's mechanics: render via the provider
# adapter, distribute into the target, stamp a manifest (just the commit id), and run
# verify_install.sh. Use it to (a) see what a correct install looks like and (b) smoke-test.
#
# Usage: build_example.sh <claude_code|codex> [target-dir]
#   target-dir   where to install (default: a fresh temp dir, printed at the end)
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE="$(git -C "$HERE" rev-parse --show-toplevel)"
ADAPTERS="$SOURCE/install/data/madagents/adapters"

PROVIDER="${1:?usage: build_example.sh <claude_code|codex> [target-dir]}"
TARGET="${2:-$(mktemp -d /tmp/madagents_example.XXXX)}"
DOCS_DST="$TARGET/.madagents/madgraph_docs"
mkdir -p "$DOCS_DST"

case "$PROVIDER" in
  claude_code|codex) ;;
  *) echo "unknown provider: $PROVIDER" >&2; exit 2 ;;
esac

# 1. Render the payload with the provider's adapter.
OUT="$(mktemp -d)"
"$ADAPTERS/$PROVIDER/render.sh" "$SOURCE" "$OUT" bare "$DOCS_DST"

# Splice the MadAgents block into an instruction file, preserving any user content.
B="<!-- MadAgents:begin -->"; E="<!-- MadAgents:end -->"
splice_block() {  # <instruction-file> <block-content-file>
  local f="$1" block="$2"
  if grep -qs "$B" "$f"; then
    sed -i "/$B/,/$E/d" "$f"; { echo; echo "$B"; cat "$block"; echo "$E"; } >> "$f"
  elif [ -f "$f" ]; then
    { echo; echo "$B"; cat "$block"; echo "$E"; } >> "$f"
  else
    mkdir -p "$(dirname "$f")"; { echo "$B"; cat "$block"; echo "$E"; } > "$f"
  fi
}

# 2. Distribute (provider-specific).
if [ "$PROVIDER" = claude_code ]; then
  mkdir -p "$TARGET/.claude/agents" "$TARGET/.claude/rules" "$TARGET/.madagents"
  splice_block "$TARGET/.claude/CLAUDE.md" "$OUT/CLAUDE.block.md"
  cp -a "$OUT/rules/."  "$TARGET/.claude/rules/"
  cp -a "$OUT/agents/." "$TARGET/.claude/agents/"
  cp -a "$OUT/system-prompt-append.md" "$TARGET/.madagents/"
else  # codex
  mkdir -p "$TARGET/.codex/agents" "$TARGET/.madagents"
  splice_block "$TARGET/AGENTS.md" "$OUT/AGENTS.block.md"
  cp -a "$OUT/agents/." "$TARGET/.codex/agents/"
  cp -a "$OUT/config.toml" "$TARGET/.codex/config.toml"
fi
cp -a "$OUT/madgraph_docs/." "$DOCS_DST/"
cp -a "$OUT/start_madagents.sh" "$TARGET/start_madagents.sh"; chmod +x "$TARGET/start_madagents.sh"
rm -rf "$OUT"

# 3. Stamp the manifest (just the source commit id + version label).
VERSION="$(git -C "$SOURCE" describe --tags --always --dirty 2>/dev/null || echo unknown)"
COMMIT="$(git -C "$SOURCE" rev-parse HEAD 2>/dev/null || echo unknown)"
MAD_VERSION="$VERSION" MAD_COMMIT="$COMMIT" MAD_PROVIDER="$PROVIDER" \
python3 - "$TARGET/.madagents/install.json" <<'PY'
import json, os, sys, datetime
json.dump({
  "version":       os.environ["MAD_VERSION"],
  "source_commit": os.environ["MAD_COMMIT"],
  "provider":      os.environ["MAD_PROVIDER"],
  "installed_at":  datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
}, open(sys.argv[1], "w"), indent=2)
PY

# 4. Verify.
echo
"$HERE/verify_install.sh" "$TARGET" "$PROVIDER"
echo
echo "Example $PROVIDER install at: $TARGET"
