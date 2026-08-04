# Install policy — the invariants, whichever CLI you are

Read by both installer agents (`.claude/skills/install/` and
`.agents/skills/install/`). The two skills are written separately and say things
their own way; **this file is the part that must not diverge**, because drift
here is the kind that deletes someone's work.

## What an install is

An **additive layer** dropped into a folder the user already owns. That folder
may be empty, may be a previous install, or may be somebody's working repository
with its own agents, its own skills and its own `CLAUDE.md`. The third case is
the one that used to get silently destroyed, and it is the case to hold in mind
throughout.

You are a guest in that folder. Everything below follows from that.

## The five invariants

### 1. Never remove or replace a path you do not own

You own exactly what you are about to record in the manifest's `paths` and
`generated`. Everything else in the folder belongs to the user.

- **Never `rm -rf` a directory.** Not `.claude/agents`, not `.claude/skills`,
  not `.agents/skills`, not anything. Install *files* by name into directories
  that may already hold other files.
- On an upgrade, the previous manifest tells you what you own. Replace those
  paths; leave every other path alone, including ones that look like ours.
- A directory that exists already is a directory you write *into*, never over.

> This is the invariant the old `installer.py` broke. `_copy_system` called
> `shutil.rmtree` on `.claude/agents` and `.claude/skills` before copying, so an
> install into a host project removed that project's own agents and skills. The
> script could not tell the difference. You can.

### 2. Copy bytes — never transcribe

Every file of the agent system is **copied**, with `cp` or `rsync`. Never read a
file and write its contents back out, never retype one, never "fix up"
formatting, never regenerate one from memory.

The reason is that the corruption would be **silent**:

- a role TOML that does not parse drops that consultant from the roster with no
  error — the consultant simply stops existing;
- a skill whose `description:` is no longer valid YAML is dropped by Codex
  without a word, so it never fires;
- both look completely fine in a directory listing.

The only files you author are the manifest and the wrapper, and the wrapper is a
mechanical substitution on a shipped template (§ below), not prose.

### 3. Report every collision by name, before writing

Before anything is written, list what is already in the folder and say it out
loud. If any path you intend to install already exists and is not yours (no
manifest, or not recorded in it), **name it and ask** — do not merge, rename or
overwrite on your own judgment.

Two that come up in practice:

- `CLAUDE.md` / `AGENTS.md` — the user's own environment description. Never
  overwrite it. Seed yours only when there is none.
- `.claude/settings.local.json` — the user may already have one. **Merge** the
  two auto-memory keys into it; do not replace the file.

Anything you *do* replace with their agreement goes in the manifest's
`replaced_with_consent`. A replacement that is not recorded there is
indistinguishable from one nobody was asked about, and the verifier fails it.

### 4. No automatic `git init`

The old installer ran `git init` on the target unasked. It had a real reason —
Claude Code resolves the project root by `.git`, and without its own root the
consultant slates are read from and written to the *enclosing* repository's
`.claude/` — but silently making someone's subdirectory a nested repository is
not yours to decide.

Explain the trade-off and let the user pick:

- `git init` the folder — clean, and correct when the folder is theirs to use
  this way;
- or leave it, and pin `autoMemoryDirectory` to an absolute path inside the
  install (Claude Code only; a Codex install has no such dependency, because
  each consultant's slate travels inside its own role file).

### 5. Always verify, and report the verdict

Write the manifest, then dispatch the **install-verifier** in a *fresh* context
and relay what it says — including warnings, including when it contradicts you.

Fresh context is not a detail. A verifier that inherits your conversation will
confirm your own account of what you did rather than read what is actually on
disk. On Codex that means `spawn_agent`, **never** `resume_agent`.

## The manifest — `.madagents/install.json`

The folder is a MadAgents install **if and only if** it has one. This replaces
the old heuristic ("`.claude/` exists"), which was true of every project anyone
had ever run Claude Code in.

```json
{
  "schema": 1,
  "provider": "claude_code",
  "memory_pack": "pretrained",
  "installed_at": "2026-08-03T11:20:00Z",
  "prompt_files": ["prompts/lead-discipline.md"],
  "disallowed_tools": [],
  "paths": {".claude/agents/mg-syntax.md": "<sha256>", "...": "..."},
  "generated": ["madagents.sh", ".claude/settings.local.json", "CLAUDE.md",
                "memory-pack.txt", ".madagents/install.json"],
  "preexisting": {"CLAUDE.md": "<sha256>", "...": "..."}
}
```

- `paths` — every byte-copied file, hashed as installed. This is what you own.
- `generated` — the files you authored. Also yours.
- `replaced_with_consent` — any path that existed *before* and that the user
  agreed to let you replace. Recording it is what makes §3 auditable.

> **Record what you copied, not what is in the directory afterwards.** After
> `cp -R` into `.claude/agents/`, that directory may hold 46 files of ours *and*
> the user's own. Build `paths` by walking the **source** and mapping each file
> to its destination — never by listing the destination. Hashing the destination
> claims their files as yours, which reads as "I overwrote this and called it
> mine", and the verifier will say so.
- `preexisting` — **hash the collision surface before you write anything.** This
  is the baseline that lets the verifier prove no host file was clobbered;
  without it that check is skipped and the install is unproven. Build it with:

  ```bash
  python3 -c "import sys; sys.path.insert(0,'<repo>/install'); \
  import installer, json, pathlib; \
  print(json.dumps(installer.hash_surface(pathlib.Path('<target>')), indent=2))"
  ```

  `installer.hash_surface` is the same definition the verifier checks against,
  so the two cannot disagree about what "the collision surface" means.

## Writing the wrapper

`madagents.sh` is the one executable you produce, so it is produced
mechanically: take the shipped template and substitute its two placeholder
lines. Nothing else in it changes.

```bash
sed -e 's|^@@PROMPT_FILES@@$|  "prompts/lead-discipline.md"|' \
    -e '/^@@DISALLOWED_TOOLS@@$/d' \
    <repo>/install/templates/madagents.sh > <target>/madagents.sh
chmod +x <target>/madagents.sh
```

(Codex: `templates/madagents-codex.sh`, which has no `@@DISALLOWED_TOOLS@@`
line.) Record `prompt_files` and `disallowed_tools` in the manifest — the
verifier re-renders the template with them and compares byte-for-byte, so any
hand-editing is caught exactly.

## When you cannot satisfy an invariant

Stop and say so. A partial install that the user understands is better than a
complete one that quietly cost them a file. There is no deadline here and
nothing is irreversible **until you write** — which is the whole reason the
survey comes first.
