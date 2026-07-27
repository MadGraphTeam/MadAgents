---
name: install-madagents
description: Install default-mode MadAgents (the multi-agent HEP setup — orchestrator, workers, reviewers) into a target folder/repo, for either Claude Code or Codex. The agent runs in the user's repo directly (bare mode). If MadAgents is already installed there, refers the user to update-madagents. Use when the user wants to set up MadAgents in a specific directory.
---

# Install MadAgents

Install the default-mode MadAgents configuration into a target directory so the user can run
it there as a normal coding-agent session — the agent works in the repo's cwd, no container.
You (the installer) run as a coding agent (Claude Code or Codex) and can install MadAgents for **either provider**:

- **claude_code** → `.claude/` (agents `.md`, `CLAUDE.md`, orchestrator via `--append-system-prompt`)
- **codex** → `AGENTS.md` + `.codex/agents/*.toml` + `.codex/config.toml`

Both assemble from the **same neutral schema** (`install/data/madagents/`) via a per-provider
adapter, so the two installs are content-equivalent. This is an **agent-driven install**:
follow the procedure precisely, adapt where the repo requires it, and confirm choices with the user.

> **Reference**: each adapter's `render.sh` (`install/data/madagents/adapters/<provider>/render.sh`)
> is the canonical renderer; `examples/build_example.sh <provider>` is a runnable end-to-end
> install; `examples/verify_install.sh` checks any finished install (step 8); the committed
> `examples/expected/<provider>/` is the golden reference to review against (step 7).

## Target layouts

```
claude_code:                          codex:
<target>/                             <target>/
  .claude/CLAUDE.md  rules/* agents/*   AGENTS.md
  .madagents/                           .codex/agents/*.toml  config.toml
    madgraph_docs/ system-prompt-…       .madagents/madgraph_docs/ install.json
    install.json                         start_madagents.sh
  start_madagents.sh
```
MadAgents content lives in a `<!-- MadAgents:begin/end -->` block inside `CLAUDE.md`/`AGENTS.md`.

## Procedure

### 1. Gather input + detect an existing install

- **Target directory** (absolute path). Offer to create it if missing.
- **Provider**: ask **claude_code or codex** (which coding agent will run MadAgents there).
- **Check for an existing install**:
  ```bash
  test -f "$TARGET/.madagents/install.json" || test -d "$TARGET/.madagents" \
    || grep -qs 'MadAgents:begin' "$TARGET/.claude/CLAUDE.md" "$TARGET/AGENTS.md"
  ```
  If any is true, **stop and refer to update**: report the installed version (from
  `install.json`) and tell the user to run **`/update-madagents`**. Do not overwrite.

### 2. Locate the source + adapter

```bash
SOURCE="$(git -C "$PWD" rev-parse --show-toplevel 2>/dev/null)"
PROVIDER="<claude_code|codex>"
RENDER="$SOURCE/install/data/madagents/adapters/$PROVIDER/render.sh"
test -f "$RENDER" || { echo "Cannot locate MadAgents source / adapter"; exit 1; }
```

### 3. Resolve target paths

```bash
TARGET="<absolute path>"
DOCS_DST="$TARGET/.madagents/madgraph_docs"
mkdir -p "$TARGET/.madagents" "$DOCS_DST"
```

### 4. Render the payload with the provider adapter

```bash
OUT="$(mktemp -d)"
"$RENDER" "$SOURCE" "$OUT" bare "$DOCS_DST"
```
- claude_code → `$OUT/{CLAUDE.block.md, rules/*, agents/*.md, system-prompt-append.md, madgraph_docs/*, start_madagents.sh}`
- codex → `$OUT/{AGENTS.block.md, agents/*.toml, config.toml, madgraph_docs/*, start_madagents.sh}`

### 5. Distribute into the target

The MadAgents instructions always go in a delimited block (so updates find them), preserving
any user content in `CLAUDE.md`/`AGENTS.md`:

```bash
B="<!-- MadAgents:begin -->"; E="<!-- MadAgents:end -->"
splice_block(){ f="$1"; block="$2"   # replace/insert the MadAgents block, keep user content
  if grep -qs "$B" "$f"; then sed -i "/$B/,/$E/d" "$f"; { echo; echo "$B"; cat "$block"; echo "$E"; } >> "$f"
  elif [ -f "$f" ]; then { echo; echo "$B"; cat "$block"; echo "$E"; } >> "$f"
  else mkdir -p "$(dirname "$f")"; { echo "$B"; cat "$block"; echo "$E"; } > "$f"; fi; }
```

**claude_code:**
```bash
mkdir -p "$TARGET/.claude/agents" "$TARGET/.claude/rules"
splice_block "$TARGET/.claude/CLAUDE.md" "$OUT/CLAUDE.block.md"
cp -a "$OUT/rules/." "$TARGET/.claude/rules/"; cp -a "$OUT/agents/." "$TARGET/.claude/agents/"
cp -a "$OUT/system-prompt-append.md" "$TARGET/.madagents/"
```
**codex:**
```bash
mkdir -p "$TARGET/.codex/agents"
splice_block "$TARGET/AGENTS.md" "$OUT/AGENTS.block.md"
cp -a "$OUT/agents/." "$TARGET/.codex/agents/"; cp -a "$OUT/config.toml" "$TARGET/.codex/config.toml"
```
**both:**
```bash
cp -a "$OUT/madgraph_docs/." "$DOCS_DST/"
cp -a "$OUT/start_madagents.sh" "$TARGET/start_madagents.sh"; chmod +x "$TARGET/start_madagents.sh"; rm -rf "$OUT"
```
On a same-name collision with a file the user already had (likely `researcher`/`plotter`),
**ask** overwrite-vs-keep first. Do not silently rename a MadAgents agent — the orchestrator routes by name.

### 6. Stamp the manifest

Save the source **commit id** + `provider` + version label. The base is **not** stored —
`update-madagents` reconstructs it from the commit id.

```bash
VERSION="$(git -C "$SOURCE" describe --tags --always --dirty 2>/dev/null || echo unknown)"
COMMIT="$(git -C "$SOURCE" rev-parse HEAD 2>/dev/null || echo unknown)"
MAD_VERSION="$VERSION" MAD_COMMIT="$COMMIT" MAD_PROVIDER="$PROVIDER" \
python3 - "$TARGET/.madagents/install.json" <<'PY'
import json, os, sys, datetime
json.dump({"version": os.environ["MAD_VERSION"], "source_commit": os.environ["MAD_COMMIT"],
  "provider": os.environ["MAD_PROVIDER"],
  "installed_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")},
  open(sys.argv[1],"w"), indent=2)
PY
```

### 7. Review the assembled setup

Beyond mechanical checks, **review** what was installed and report a short summary to the user:

- **Agent set**: all 8 agents present (`script-operator, physics-expert, plotter, pdf-reader,
  researcher, presentation-reviewer, verification-reviewer, madgraph-operator`).
- **Routing coherence**: every worker the orchestrator routes to (in the `<worker_routing>`
  block of `CLAUDE.md`/`AGENTS.md`) names an agent that actually exists.
- **Operator docs**: `madgraph-operator` references `{{DOCS}}`-substituted paths (the real
  `.madagents/madgraph_docs`), and the curated overview is present in its body.
- **Cleanliness**: no leftover `{{…}}` placeholders or `container-only` markers.
- **Reference compare** (optional): the rendered agents/instructions should match the structure
  of `install/data/madagents/examples/expected/$PROVIDER/` (the golden reference, modulo the
  `<DOCS>` token vs the real docs path). For Codex, confirm every `.codex/agents/*.toml` parses.

If anything looks off, fix it before reporting success.

### 8. Verify and finish

```bash
"$SOURCE/install/data/madagents/examples/verify_install.sh" "$TARGET" "$PROVIDER"
```
Report the result, then tell the user: `cd <target> && ./start_madagents.sh`
(launches `claude` or `codex` accordingly).

### 9. Offer a `.gitignore` update (ask first)

**Ask** before editing `.gitignore`. Propose `.madagents/` and `start_madagents.sh` (and ask
about the `.claude/`/`.codex/` additions). Append idempotently; create the file if absent.

## Notes

- **Merge, don't clobber**: existing `.claude/`/`.codex/`/instruction files are preserved
  (block-spliced; same-name files replaced only with consent).
- Default mode only: no extra skills, no verify/doc-editing agents.
- Already installed? → **`/update-madagents`**.
- Container mode is deferred — see `install/data/madagents/adapters/claude_code/CONTAINER_DEFERRED.md`.
- **Codex caveat**: Codex spawns subagents only on *explicit* request (no implicit
  auto-delegation). The orchestrator instructions in `AGENTS.md` drive this; if delegation
  is unreliable in practice, that prompt is where to tune it.
