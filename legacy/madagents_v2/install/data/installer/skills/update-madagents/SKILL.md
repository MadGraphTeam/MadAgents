---
name: update-madagents
description: Update an existing MadAgents install in a repo to the current source version, preserving the user's edits via a 3-way merge (base = the version they installed, current = their files, new = the current version). Reconstructs the original from git history — no local snapshot. Use when MadAgents is already installed and the user wants to update it.
---

# Update MadAgents

Update an existing install in place. The core idea is a **3-way merge** per file:

- **base** = the pristine original of the version the user installed — *reconstructed* by
  rendering that version's templates from git history (not a local copy the user could edit).
- **current** = what's in the repo now (base + the user's edits).
- **new** = the current version, freshly rendered.

`git merge-file current base new` then does the right thing per file: unchanged → take new;
user-edited only → keep theirs; both → merge (clean keeps both; overlapping → conflict).

> Uses the same per-provider `adapters/<provider>/render.sh` as install, so base and new render
> identically — the only differences come from the version change itself.

## Procedure

### 1. Detect the install and read the manifest

```bash
TARGET="<repo path>"; MANIFEST="$TARGET/.madagents/install.json"
test -f "$MANIFEST" || { echo "No manifest — see Legacy fallback"; }
get(){ python3 -c "import json,sys;print(json.load(open('$MANIFEST')).get(sys.argv[1],''))" "$1"; }
COMMIT="$(get source_commit)"; INSTALLED="$(get version)"      # the commit id is all we need
PROVIDER="$(get provider)"; [ -n "$PROVIDER" ] || PROVIDER=claude_code   # legacy installs = claude_code
DOCS_DST="$TARGET/.madagents/madgraph_docs"; DOCS="$DOCS_DST"   # derived from the target, not stored
# Provider-specific instruction file + its block-payload name:
if [ "$PROVIDER" = codex ]; then IFILE="$TARGET/AGENTS.md"; IBLOCK="AGENTS.block.md"
else IFILE="$TARGET/.claude/CLAUDE.md"; IBLOCK="CLAUDE.block.md"; fi
```

### 2. Locate source, compare versions

```bash
SOURCE="$(git -C "$PWD" rev-parse --show-toplevel)"
RENDER="$SOURCE/install/data/madagents/adapters/$PROVIDER/render.sh"
NEW_VERSION="$(git -C "$SOURCE" describe --tags --always --dirty)"
NEW_COMMIT="$(git -C "$SOURCE" rev-parse HEAD)"
[ "$NEW_COMMIT" = "$COMMIT" ] && { echo "Already at $INSTALLED — up to date."; exit 0; }
echo "Updating: $INSTALLED  ->  $NEW_VERSION"
```

### 3. Reconstruct base, render new

The installed version's files are still in this repo's git history. Pull **only** the two
paths the renderer reads — the templates and the docs — at the recorded commit (no checkout,
no whole-tree extraction, no network), then render both versions with the current `render.sh`:

```bash
BASE_SRC="$(mktemp -d)"
git -C "$SOURCE" archive "$COMMIT" -- \
  install/data/madagents src/madagents/software_instructions \
  | tar -x -C "$BASE_SRC" \
  || { echo "commit $COMMIT not in this repo's history — see Legacy fallback"; exit 1; }
BASE="$(mktemp -d)"; NEW="$(mktemp -d)"
"$RENDER" "$BASE_SRC" "$BASE" bare "$DOCS"   # vN templates, rendered now
"$RENDER" "$SOURCE"   "$NEW"  bare "$DOCS"   # current templates
```

(This renders the old templates with the *current* renderer — minimal, and correct as long
as `render.sh`'s transform is stable. If the renderer itself ever changes incompatibly, render
`BASE` with `$BASE_SRC/install/data/madagents/adapters/$PROVIDER/render.sh` instead.)

### 4. Map a payload path to its live target path

```bash
map(){ case "$1" in
  start_madagents.sh) echo "$TARGET/start_madagents.sh"; return ;;
  madgraph_docs/*)    echo "$TARGET/.madagents/$1";       return ;;
esac
if [ "$PROVIDER" = codex ]; then
  case "$1" in
    config.toml) echo "$TARGET/.codex/config.toml" ;;
    agents/*)    echo "$TARGET/.codex/$1" ;;             # agents/<name>.toml -> .codex/agents/<name>.toml
    *) echo "" ;;
  esac
else
  case "$1" in
    system-prompt-append.md) echo "$TARGET/.madagents/system-prompt-append.md" ;;
    rules/*|agents/*)        echo "$TARGET/.claude/$1" ;;
    *) echo "" ;;
  esac
fi; }
```

### 5. Ask about backups (once)

List the files the user has modified (`live` differs from `base`) and the CLAUDE block, then
ask **once** whether to back them up. Conflicts are always backed up regardless.

```bash
BACKUP=1   # set from the user's answer (1=yes, 0=no)
```

### 6. Merge every file (go file-by-file)

```bash
B="<!-- MadAgents:begin -->"; E="<!-- MadAgents:end -->"; CM="$IFILE"   # CLAUDE.md or AGENTS.md

# 6a. instruction block (merge only the delimited block; user content outside is untouched).
awk -v b="$B" -v e="$E" 'index($0,b){f=1;next} index($0,e){f=0} f' "$CM" > /tmp/cur_block
git merge-file -p /tmp/cur_block "$BASE/$IBLOCK" "$NEW/$IBLOCK" > /tmp/merged_block; rc=$?
{ [ "$BACKUP" = 1 ] && ! cmp -s /tmp/cur_block "$BASE/$IBLOCK"; } || [ $rc -ne 0 ] && cp "$CM" "$CM.orig"
python3 - "$CM" "$B" "$E" /tmp/merged_block <<'PY'
import sys
cm,B,E,mb=sys.argv[1:5]; src=open(cm).read().splitlines(); merged=open(mb).read().splitlines()
out=[]; i=0; n=len(src); done=False
while i<n:
    if not done and src[i].strip()==B.strip():
        out.append(src[i]); out+=merged
        j=i+1
        while j<n and src[j].strip()!=E.strip(): j+=1
        if j<n: out.append(src[j])
        i=j+1; done=True
    else: out.append(src[i]); i+=1
open(cm,"w").write("\n".join(out)+"\n")
PY
[ $rc -ne 0 ] && echo "CONFLICT in CLAUDE block (markers left in $CM; backup at $CM.orig)"

# 6b. Every other payload file present in base AND new.
while read -r rel; do
  [ "$rel" = "$IBLOCK" ] && continue
  live="$(map "$rel")"; [ -n "$live" ] || continue
  base="$BASE/$rel"; new="$NEW/$rel"
  if [ ! -f "$base" ]; then           # added in new version
    if [ -e "$live" ]; then cp "$live" "$live.orig"; echo "ADDED (had local file, backed up): $rel"; fi
    mkdir -p "$(dirname "$live")"; cp "$new" "$live"; continue
  fi
  [ -f "$live" ] || { mkdir -p "$(dirname "$live")"; cp "$new" "$live"; continue; }  # user deleted → restore new
  modified=1; cmp -s "$live" "$base" && modified=0
  git merge-file -p "$live" "$base" "$new" > "$live.m" 2>/dev/null; rc=$?
  { [ "$BACKUP" = 1 ] && [ "$modified" = 1 ]; } || [ $rc -ne 0 ] && cp "$live" "$live.orig"
  mv "$live.m" "$live"
  [ $rc -ne 0 ] && echo "CONFLICT (markers left, backup .orig): $rel"
done < <(cd "$NEW" && find . -type f | sed 's|^\./||')
```

### 7. Remove files dropped by the new version

For each payload file in `base` but **not** in `new`: if the user never touched it
(`live == base`) → delete it; otherwise keep it and report (don't destroy their edits).

```bash
while read -r rel; do
  [ "$rel" = "$IBLOCK" ] && continue
  [ -f "$NEW/$rel" ] && continue
  live="$(map "$rel")"; [ -n "$live" ] && [ -f "$live" ] || continue
  if cmp -s "$live" "$BASE/$rel"; then rm -f "$live"; echo "REMOVED (dropped by new version): $rel"
  else echo "KEPT (dropped by new version but you edited it): $rel"; fi
done < <(cd "$BASE" && find . -type f | sed 's|^\./||')
```

### 8. Refresh the manifest, clean up, verify

Rewrite `install.json` with the new `version`/`source_commit` (keep `provider`), remove
temp dirs, then run the verifier and report — listing every `.orig` backup and any remaining
conflict markers for the user to resolve.

```bash
rm -rf "$BASE_SRC" "$BASE" "$NEW"
# (rewrite install.json: set version=$NEW_VERSION, source_commit=$NEW_COMMIT, installed_at=now)
"$SOURCE/install/data/madagents/examples/verify_install.sh" "$TARGET" "$PROVIDER"
```

## Legacy fallback (no `install.json`)

There's no recorded version to reconstruct a base from, so a clean 3-way merge isn't possible.
Tell the user, then offer:
1. **Ask which version they installed** (a tag/commit), set `COMMIT` from it, and proceed normally.
2. **Back up + reinstall**: move the existing MadAgents files aside (`.orig`), run a fresh
   `install-madagents` at the current version, and let the user re-apply any edits from the backups.

## Notes

- Everything MadAgents installed is treated as user-editable and merged (agents, rules, the
  CLAUDE block, **docs**, launcher) — nothing is blind-overwritten.
- The user's own non-MadAgents files and content outside the CLAUDE block are never touched.
- Conflicts leave standard `<<<<<<<`/`>>>>>>>` markers in the file plus a `.orig` backup.
