---
name: install
description: Install the MadAgents agent system into a folder on this machine, to be run without a container. Use when the user wants MadAgents outside Apptainer — in a project folder, on a login node, or anywhere they already have MadGraph — or wants to refresh or check an existing install.
---

# Install MadAgents into a folder

Your working directory is `install/`; the repo root is `..`. **You** perform the
install — there is no installer script any more. What is left of `installer.py`
is a read-only `verify` command.

**Read `install-policy.md` before you write anything.** It holds the five
invariants (never remove what you do not own; copy bytes, never transcribe;
report collisions by name; no automatic `git init`; always verify) and the
manifest format. This file is the procedure; that one is the contract — the same
contract the Codex installer works to.

In `install/` beside the policy, read on demand:

- `example-install.md` — a finished install in full: the tree, the wrapper, the
  settings, the manifest. Open it to check a result or to show the user what
  landed.
- `troubleshooting.md` — the failure modes and how to tell them apart. Several
  look identical from the outside.

(Both are shared with the Codex installer — they describe the artifact, which is
the same one whichever CLI built it.)

## 1. Ask, then survey — and survey before you write

**Where.** The folder to install into. It becomes the session's project root, so
it should be the folder the user will actually work in. Accept `~`.

**Which memory pack.** List them from the source of truth, not from memory:

```bash
python3 -c "import sys; sys.path.insert(0,'../src'); from launcher.setup import memory_options; [print(f'{n:18} {d}') for n, d in memory_options()]"
```

`pretrained` is the default and right for Anthropic models; the `-local` packs
are for a self-hosted model; `none` starts cold.

**Which CLI to install *for*.** `claude_code` (default) or `codex` — whichever
the user has installed and authenticated. This is independent of which CLI *you*
run under: you are Claude Code, and you can install either. An install belongs to
one provider, and there is no conversion afterwards.

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

**A `.claude/` directory is not evidence of a MadAgents install.** Every project
anyone has ever run Claude Code in has one. The manifest is the only evidence.
Getting this wrong is what used to delete people's agents and skills.

## 3. Fresh install

Source is `../madagents/` for `claude_code`, `../madagents_codex/` for `codex`.
Take the pre-install baseline first — even on a folder you believe is empty:

```bash
mkdir -p <target>
python3 -c "import sys,json,pathlib; sys.path.insert(0,'.'); import installer; \
print(json.dumps(installer.hash_surface(pathlib.Path('<target>')), indent=2))" > /tmp/preexisting.json
```

Then copy. **`cp`, never transcribe** — and copy *into* directories, never over
them:

```bash
# claude_code
mkdir -p <target>/.claude
cp -R ../madagents/.claude/agents <target>/.claude/
cp -R ../madagents/.claude/skills <target>/.claude/
cp -R ../madagents/prompts        <target>/
cp    ../madagents/config.yaml    <target>/

# codex
mkdir -p <target>/.codex <target>/.agents
cp -R ../madagents_codex/.codex/agents      <target>/.codex/
cp    ../madagents_codex/.codex/config.toml <target>/.codex/
cp -R ../madagents_codex/.agents/skills     <target>/.agents/
cp -R ../madagents_codex/prompts            <target>/
cp    ../madagents_codex/config.yaml        <target>/
cp    templates/lead-slate-header.md        <target>/prompts/
```

**Memory.** The packs keep their Claude Code shape and serve both providers:

| Pack path | `claude_code` | `codex` |
|---|---|---|
| `.claude/lead-memory` | `.claude/lead-memory` | `.madagents/memory/lead` |
| `.claude/agent-memory` | `.claude/agent-memory` | *spliced into the role files* |
| `.madagents/wiki` | `.madagents/wiki` | `.madagents/wiki` |

Create `.madagents/wiki/{consultants,lead}` either way, so the layout does not
depend on the pack. Write `memory-pack.txt` with the pack name.

**Codex slates are the one thing you do not copy.** Each consultant's slate lives
inside its own role TOML, and a malformed write drops that consultant from the
roster silently. Never edit those files by hand — call the tool that owns the
splice, which re-parses the whole file before writing:

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

A **cold** Codex install needs none of this: the shipped role files already carry
the empty slate skeleton.

**The wrapper** — the mechanical substitution from the policy, nothing authored:

```bash
sed -e 's|^@@PROMPT_FILES@@$|  "prompts/lead-discipline.md"|' \
    -e '/^@@DISALLOWED_TOOLS@@$/d' \
    templates/madagents.sh > <target>/madagents.sh     # codex: madagents-codex.sh
chmod +x <target>/madagents.sh
```

**Settings** — Claude Code only, and **merge if the file already exists**:

```bash
sed 's|@@LEAD_MEMORY_ABS@@|<abs>/.claude/lead-memory|' \
    templates/settings.local.json > <target>/.claude/settings.local.json
```

**Environment description.** Copy `templates/environment.md` to
`<target>/CLAUDE.md` (`AGENTS.md` on Codex) — **only if there is none**. It
asserts no MadGraph path on purpose: on this machine MadGraph is wherever the
user has it, or nowhere, and the session records what it finds. Fill in a path
only if the user gives you one; never guess.

**git.** Do not run `git init` unasked. Explain the trade-off from the policy and
let the user choose.

## 4. Upgrade an existing install

The old manifest says what you own. Replace exactly those `paths`; keep the
learned tier (`.claude/agent-memory`, `.claude/lead-memory`,
`.madagents/memory`, `.madagents/wiki`), keep `CLAUDE.md`/`AGENTS.md` and
`memory-pack.txt`, and touch nothing else.

**On Codex a role file is card and slate at once**, so overwriting it discards
what that consultant learned. For each role: read the slate out, copy the new
card in, write the slate back — `codex_memory.read_slate` / `write_slate` do it
safely, with a full TOML re-parse before the file is replaced. Report any role
the new release no longer ships; removing it removes its slate with it.

## 5. Additive install into the user's own project

Everything in §3, with the policy's constraints in force:

- List every path you intend to write **that already exists**, by name, and ask
  before touching any of it.
- Never replace `.claude/agents/` or `.claude/skills/` as directories — copy the
  46 agents and 8 skills in *beside* whatever is already there.
- Leave their `CLAUDE.md` alone; offer to append an Environment section instead.
- Merge into their `settings.local.json`; never overwrite it.
- Their `.git` is theirs. This is where `git init` is most likely wrong and
  pinning `autoMemoryDirectory` absolutely is most likely right.

## 6. Manifest, verify, report

Write `<target>/.madagents/install.json` in the policy's format — `paths` (every
copied file with its sha256), `generated`, `prompt_files`, `disallowed_tools`,
and `preexisting` from the baseline you took in §3.

```bash
python3 installer.py verify <target>
```

Then dispatch **install-verifier** in a fresh context to judge what a checksum
cannot, and relay what it says — including its warnings, and including where it
disagrees with you. If it fails, fix and re-verify rather than explaining the
failure away.

Close with the three things the verifier cannot do for them:

- **Start it:** `cd <target> && ./madagents.sh`. A bare `claude` (or `codex`) in
  that folder works too but is not the full system — the wrapper is what appends
  the lead's system prompt.
- **On a Codex install:** Codex asks whether to trust the folder on the first run
  there. Say so up front — untrusted, it ignores `.codex/` and the 46 consultants
  silently do not exist, which looks like plain Codex rather than an error.
- **MadGraph:** the seeded environment file records that its location is unknown
  and asks the session to fill it in. If the user tells you where it is, offer to
  write that one line. Otherwise leave it for the first session to find out.

If the user has no MadGraph on this machine at all, do not let that go unsaid:
the system installs and runs, but everything it exists to do against a real
MadGraph needs one, and the container path (`./madrun.sh`) brings its own.
`troubleshooting.md` has how to put that without deciding it for them.
