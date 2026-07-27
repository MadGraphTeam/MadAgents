#!/usr/bin/env bash
# Verify a MadAgents install in a target directory, for either provider.
#
# Usage: verify_install.sh <target-dir> <claude_code|codex>
#
# Exits 0 if all checks pass, 1 otherwise. Used by the install/update skills and as a smoke test.
set -uo pipefail

TARGET="${1:?usage: verify_install.sh <target-dir> <claude_code|codex>}"
PROVIDER="${2:?usage: verify_install.sh <target-dir> <claude_code|codex>}"

MAD="$TARGET/.madagents"
DOCS="$MAD/madgraph_docs"
LAUNCH="$TARGET/start_madagents.sh"
AGENTS=(script-operator physics-expert plotter pdf-reader researcher
        presentation-reviewer verification-reviewer madgraph-operator)

fail=0
ok()   { printf '  \033[32mOK\033[0m   %s\n' "$1"; }
bad()  { printf '  \033[31mFAIL\033[0m %s\n' "$1"; fail=1; }
check(){ if eval "$2"; then ok "$1"; else bad "$1"; fi; }

echo "Verifying MadAgents install: $TARGET ($PROVIDER)"

# ── shared ───────────────────────────────────────────────────────────
check "docs copied (non-empty)"          "[ -n \"\$(ls -A '$DOCS' 2>/dev/null)\" ]"
check "launcher executable"              "[ -x '$LAUNCH' ]"
check "launcher parses"                  "bash -n '$LAUNCH'"
check "manifest present"                 "[ -f '$MAD/install.json' ]"
check "manifest valid JSON w/ version"   "python3 -c \"import json,sys;d=json.load(open('$MAD/install.json'));sys.exit(0 if d.get('version') else 1)\""

if [ "$PROVIDER" = claude_code ]; then
  CLAUDE="$TARGET/.claude"
  check ".madagents/system-prompt-append.md" "[ -f '$MAD/system-prompt-append.md' ]"
  check ".claude/CLAUDE.md exists"        "[ -f '$CLAUDE/CLAUDE.md' ]"
  check "CLAUDE.md has MadAgents block"   "grep -q 'MadAgents:begin' '$CLAUDE/CLAUDE.md' && grep -q 'MadAgents:end' '$CLAUDE/CLAUDE.md'"
  check "rules/correctness.md"            "[ -f '$CLAUDE/rules/correctness.md' ]"
  check "rules/mandatory-reviews.md"      "[ -f '$CLAUDE/rules/mandatory-reviews.md' ]"
  for a in "${AGENTS[@]}"; do
    check "agent: $a"                     "[ -f '$CLAUDE/agents/$a.md' ]"
  done
  check "operator card has overview"      "grep -q 'MadGraph5_aMC' '$CLAUDE/agents/madgraph-operator.md'"
  check "no leftover placeholders/markers" "! grep -rqE '{{|container-only' '$CLAUDE'"

elif [ "$PROVIDER" = codex ]; then
  CODEX="$TARGET/.codex"
  check "AGENTS.md exists"                "[ -f '$TARGET/AGENTS.md' ]"
  check "AGENTS.md has MadAgents block"   "grep -q 'MadAgents:begin' '$TARGET/AGENTS.md' && grep -q 'MadAgents:end' '$TARGET/AGENTS.md'"
  check ".codex/config.toml exists"       "[ -f '$CODEX/config.toml' ]"
  for a in "${AGENTS[@]}"; do
    check "agent toml: $a"                "[ -f '$CODEX/agents/$a.toml' ]"
  done
  check "all agent TOMLs parse"           "python3 -c \"import tomllib,glob,sys; sys.exit(0 if all(tomllib.load(open(f,'rb')).get('developer_instructions') for f in glob.glob('$CODEX/agents/*.toml')) else 1)\""
  check "operator toml has overview"      "grep -q 'MadGraph5_aMC' '$CODEX/agents/madgraph-operator.toml'"
  check "no leftover placeholders/markers" "! grep -rqE '{{|container-only' '$CODEX' '$TARGET/AGENTS.md'"

else
  bad "unknown provider: $PROVIDER (expected claude_code|codex)"
fi

if [ "$fail" -eq 0 ]; then
  printf '\033[32mAll checks passed.\033[0m\n'; exit 0
else
  printf '\033[31mSome checks failed.\033[0m\n'; exit 1
fi
