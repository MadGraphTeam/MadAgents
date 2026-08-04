---
name: install
description: 'Install the MadAgents agent system into a folder on this machine, to be run without a container. Use when the user wants MadAgents outside Apptainer — in a project folder, on a login node, or anywhere they already have MadGraph — or wants to refresh or check an existing install.'
---

# Install MadAgents into a folder

Your working directory is `install/`; the repo root is `..`. **You** perform the
install — there is no installer script. What is left of `installer.py` is a
read-only `verify` command.

**Read `install-policy.md` before you write anything.** It holds the five
invariants (never remove what you do not own; copy bytes, never transcribe;
report collisions by name; no automatic `git init`; always verify) and the
manifest format. This file is the procedure; that one is the contract, and the
Claude Code installer works to the same one.

In `install/` beside the policy, read on demand:

- `example-install.md` — a finished install in full: the tree, the wrapper, the
  manifest.
- `troubleshooting.md` — the failure modes and how to tell them apart.

## 1. Ask, then survey — and survey before you write

**Where.** The folder to install into. It becomes the project root, so it should
be the folder the user will actually work in. Accept `~`.

**Which memory pack.** List them from the source of truth, not from memory:

```bash
python3 -c "import sys; sys.path.insert(0,'../src'); from launcher.setup import memory_options; [print(f'{n:18} {d}') for n, d in memory_options()]"
```

`pretrained` is the default and right for Anthropic models; the `-local` packs
are for a self-hosted model; `none` starts cold.

**Which CLI to install *for*.** `codex` or `claude_code`. This is independent of
which CLI *you* run under: you are Codex, and you can install either. An install
belongs to one provider, and there is no conversion afterwards.

Then **survey the target and report what you find before writing anything**:

```bash
ls -A <target> 2>/dev/null
cat <target>/.madagents/install.json 2>/dev/null
```

## 2. Classify — the step that used to be a bad guess

| What you see | What it is | What you do |
|---|---|---|
| Folder empty or absent | a fresh install | §3 |
| `.madagents/install.json` present | an existing MadAgents install | §4, upgrade |
| Files present, **no** manifest | **the user's own project** | §5, additive — ask first |

**A `.codex/` or `.claude/` directory is not evidence of a MadAgents install.**
Any project someone has used either CLI in has one. The manifest is the only
evidence, and getting this wrong is what used to delete people's work.

## 3. Fresh install

Source is `../madagents_codex/` for `codex`, `../madagents/` for `claude_code`.
Take the pre-install baseline first — even on a folder you believe is empty:

```bash
mkdir -p <target>
python3 -c "import sys,json,pathlib; sys.path.insert(0,'.'); import installer; \
print(json.dumps(installer.hash_surface(pathlib.Path('<target>')), indent=2))" > /tmp/preexisting.json
```

Then copy. **`cp`, never transcribe** — and copy *into* directories, never over
them:

```bash
# codex
mkdir -p <target>/.codex <target>/.agents
cp -R ../madagents_codex/.codex/agents      <target>/.codex/
cp    ../madagents_codex/.codex/config.toml <target>/.codex/
cp -R ../madagents_codex/.agents/skills     <target>/.agents/
cp -R ../madagents_codex/prompts            <target>/
cp    ../madagents_codex/config.yaml        <target>/
cp    templates/lead-slate-header.md        <target>/prompts/

# claude_code
mkdir -p <target>/.claude
cp -R ../madagents/.claude/agents <target>/.claude/
cp -R ../madagents/.claude/skills <target>/.claude/
cp -R ../madagents/prompts        <target>/
cp    ../madagents/config.yaml    <target>/
```

**Memory.** The packs keep their Claude Code shape and serve both providers:

| Pack path | `codex` | `claude_code` |
|---|---|---|
| `.claude/lead-memory` | `.madagents/memory/lead` | `.claude/lead-memory` |
| `.claude/agent-memory` | *spliced into the role files* | `.claude/agent-memory` |
| `.madagents/wiki` | `.madagents/wiki` | `.madagents/wiki` |

Create `.madagents/wiki/{consultants,lead}` either way. Write `memory-pack.txt`
with the pack name.

**The consultant slates are the one thing you do not copy.** On Codex each lives
*inside* its own role TOML, and a malformed write drops that consultant from the
roster with no error — the file still exists and the consultant simply stops
being dispatchable. Never hand-edit a role file. Call the tool that owns the
splice, which re-parses the whole file before replacing it:

```bash
python3 -c "import sys; sys.path.insert(0,'../src'); from pathlib import Path; \
from launcher.setup import _seed_codex_slates; \
_seed_codex_slates(Path('../memory/<pack>'), Path('<target>'))"
```

Use `_seed_codex_slates`, **not** `codex_memory.seed_slates` directly. Five roles
(the reviewers and auditors) carry no slate region at all — they have no
`memory:` on the Claude Code side, so the renderer gives them none — and the raw
function raises on them. The wrapper skips those and gives every other role the
cold skeleton where the pack has nothing, which is what makes the pack *replace*
the learned tier rather than show through where it is thin.

A **cold** install needs none of this: the shipped role files already carry the
empty slate skeleton.

**The wrapper** — the mechanical substitution from the policy, nothing authored:

```bash
sed 's|^@@PROMPT_FILES@@$|  "prompts/lead-discipline.md"|' \
    templates/madagents-codex.sh > <target>/madagents.sh
chmod +x <target>/madagents.sh
```

(For a `claude_code` install use `templates/madagents.sh`, which additionally has
a `@@DISALLOWED_TOOLS@@` line to delete, and write
`.claude/settings.local.json` from `templates/settings.local.json` — **merging**
if the user already has one.)

**Environment description.** Copy `templates/environment.md` to
`<target>/AGENTS.md` (`CLAUDE.md` for a Claude Code install) — **only if there is
none**. It asserts no MadGraph path on purpose. Fill one in only if the user
gives it to you; never guess.

**git.** Do not run `git init` unasked. A Codex install does not depend on it the
way a Claude Code one does — each consultant's slate travels inside its own role
file, so there is no absolute path to pin — but Codex still resolves the project
root by `.git`, which decides where `AGENTS.md` is merged from. Explain it and let
the user choose.

## 4. Upgrade an existing install

The old manifest says what you own. Replace exactly those `paths`; keep the
learned tier (`.madagents/memory`, `.madagents/wiki`), keep `AGENTS.md` and
`memory-pack.txt`, and touch nothing else.

**A Codex role file is card and slate at once**, so copying the new one over it
discards what that consultant learned. For each role: read the slate out, copy
the new card in, write the slate back —

```bash
python3 -c "import sys; sys.path.insert(0,'../src'); from launcher import codex_memory; \
from pathlib import Path; p = Path('<target>/.codex/agents/<role>.toml'); \
print(codex_memory.read_slate(p))"
```

then `cp` the new card and `codex_memory.write_slate(p, saved)`, which re-parses
before writing. Report any role the new release no longer ships — removing it
removes its slate with it.

## 5. Additive install into the user's own project

Everything in §3, with the policy's constraints in force:

- List every path you intend to write **that already exists**, by name, and ask
  before touching any of it.
- Never replace `.codex/agents/` or `.agents/skills/` as directories — copy the
  46 roles and 8 skills in *beside* whatever is already there.
- Leave their `AGENTS.md` alone; offer to append an Environment section instead.
  Theirs loads into every agent in that project, so overwriting it changes how
  their own sessions behave, not just ours.
- Their `.git` is theirs.

## 6. Manifest, verify, report

Write `<target>/.madagents/install.json` in the policy's format — `paths` (every
copied file with its sha256), `generated`, `prompt_files`, `disallowed_tools`,
and `preexisting` from the baseline you took in §3.

```bash
python3 installer.py verify <target>
```

Then `spawn_agent` **install-verifier** to judge what a checksum cannot, and
relay what it says — warnings included, and including where it disagrees with
you. **Never `resume_agent` it**: a resumed thread carries your history and would
confirm your own account instead of reading the disk. If it fails, fix and
re-verify rather than explaining the failure away.

Close with the three things the verifier cannot do for them:

- **Start it:** `cd <target> && ./madagents.sh`. A bare `codex` in that folder
  works too but is not the full system — the wrapper is what supplies the lead's
  instructions and appends its slate.
- **Trust:** Codex asks whether to trust the folder on the first run there. Say so
  up front — untrusted, it ignores `.codex/` entirely and the 46 consultants
  silently do not exist, which looks like plain Codex rather than an error.
- **MadGraph:** the seeded `AGENTS.md` records that its location is unknown and
  asks the session to fill it in. If the user tells you where it is, offer to
  write that one line. Otherwise leave it for the first session to find out.

If the user has no MadGraph on this machine at all, do not let that go unsaid:
the system installs and runs, but everything it exists to do against a real
MadGraph needs one, and the container path (`./madrun.sh`) brings its own.
