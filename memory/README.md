# Memory packs

The agent system in [`madagents/`](../madagents) ships **cold**: the full surface (46 consultant
subagents, 8 skills, the lead's system prompt) but an empty learned tier. A **memory pack** is that
learned tier — what the system accumulated by working on MadGraph tasks — kept separately so you can
choose how much of it a run starts with.

Packs are **stored once, in the Claude Code layout**, and the setup path translates as it seeds — so
one pack serves every CLI. On Claude Code and on opencode the files land where they are: the wiki in
`.madagents/wiki/`, one slate per consultant at `.claude/agent-memory/<name>/MEMORY.md` (opencode
pulls each into its agent's prompt by `{file:}` interpolation, so no translation is needed at all).
On Codex the lead's slate becomes `.madagents/memory/lead/MEMORY.md` and each consultant's is
spliced into the marked region of its own `.codex/agents/<name>.toml`, which is what Codex
auto-loads for that role. Nothing about *choosing* a pack changes — except along the one axis below
that genuinely is per-CLI.

```bash
./madrun.sh                             # interactive: pick the memory from a menu
./madrun.sh --list-memory               # what each option carries, then exit
./madrun.sh --new --memory pretrained   # default: warm, for Anthropic models
./madrun.sh --new --memory none         # fully cold
# self-hosted models — pick the pair matching the CLI the run is built for:
./local/madrun.sh --new --memory pretrained-local-opencode   # warm, opencode
./local/madrun.sh --new --memory bare-local-opencode         # cold domain, opencode
```

## The packs

| Pack | MadGraph knowledge | Harness know-how | For |
| --- | --- | --- | --- |
| [`pretrained`](pretrained) | ✔ 38 populated slates, 592 wiki pages | ✘ | Anthropic models (Opus, Sonnet) |
| [`pretrained-local-cc`](pretrained-local-cc) | ✔ same | ✔ Claude Code | a self-hosted model on Claude Code |
| [`bare-local-cc`](bare-local-cc) | ✘ | ✔ Claude Code | as above, cold domain |
| [`pretrained-local-opencode`](pretrained-local-opencode) | ✔ same | ✔ opencode | a self-hosted model on opencode |
| [`bare-local-opencode`](bare-local-opencode) | ✘ | ✔ opencode | as above, cold domain |

The two axes are independent, which is what makes the set a matrix rather than a ladder:

- **MadGraph knowledge** — 46 per-consultant slates, a 592-page wiki, and the lead's routing index.
  This is the substance: source-grounded MG5 facts the system worked out and wrote down. It is
  **provider-neutral**: MG5 behaves the same whichever CLI is asking.
- **Harness know-how** — one lead-memory principle on how a dispatched subagent's work comes back.
  Frontier Anthropic models already do this correctly, so carrying it costs context and buys
  nothing; a smaller self-hosted model benefits from having it stated. Each `pretrained-local-*` is
  exactly `pretrained` plus that principle, and each `bare-local-*` is exactly that principle alone.

**This is the one axis that is *not* provider-neutral, which is why those packs carry a suffix.**
Claude Code delivers a subagent's result by re-invoking the lead with a `<task-notification>` after
it ends its turn; opencode returns the reply as the `task` call's own result, in the same turn.
Stating Claude Code's mechanic to an opencode lead is worse than saying nothing: it would end its
turn waiting to be re-invoked and simply stop, losing the dispatched work. Nothing detects that for
you — the seeding is mechanical — so **match the suffix to the run's `--provider`**.

The remaining combination — no MadGraph knowledge *and* no harness know-how — is the shipped system
as-is, so it needs no pack: that is `--memory none`.

A pack does **not** select the model. Which model a run talks to is settled before the session
starts; the two `-local` packs are the memory you would pair with that choice, not the thing that
makes it.

## Fixed in the repo, extended in the run

A pack in this directory is **read-only reference state**. `madrun.sh` copies it into the run
instance it builds, and the running agent reads and writes only that copy:

```
memory/pretrained/.claude/lead-memory/    ─┐
memory/pretrained/.claude/agent-memory/    ├─ copied at setup ─→  run_dir/instances/<name>__<stamp>/
memory/pretrained/.madagents/wiki/        ─┘                        .claude/{lead-memory,agent-memory}/
                                                                    output/.madagents/wiki/
```

So a session extends the memory it was given — new wiki pages, revised slates, new lead playbooks —
and none of it touches this directory. Nothing at runtime is bound to `memory/`; the packs cannot be
written back to by accident.

To carry an extended memory into a *further* session, fork the instance instead of re-seeding:

```bash
./madrun.sh                                        # then pick "f) fork an existing run"
./madrun.sh --fork run_dir/instances/<name>__<stamp>   # or name it directly
```

A fork keeps the learned tier (slates, lead memory, wiki) and drops the run's deliverables. To
promote one of your own runs into a permanent pack, copy those three trees into a new
`memory/<name>/` in the same layout, and add a one-line `memory/<name>/DESCRIPTION`.

## How a pack introduces itself

Each pack carries its own one-line summary in `memory/<pack>/DESCRIPTION`. That file is what the
launcher prints — in the interactive menu and in `./madrun.sh --list-memory` — so descriptions live
with the packs rather than hardcoded in the launcher, and a pack you drop into `memory/` shows up
explaining itself with no code change. A pack with no `DESCRIPTION` still works; it just lists
without a summary. `none` has no directory, so its description is a constant in
`src/launcher/setup.py`.

## Where it lands at run time

The instance's `output/` is the session's project root (`/output` in the container), so:

| In a pack | At run time |
| --- | --- |
| `.claude/lead-memory/` | `/output/.claude/lead-memory/` — the lead's own slate + playbooks |
| `.claude/agent-memory/<agent>/MEMORY.md` | `/output/.claude/agent-memory/<agent>/MEMORY.md` — one slate per consultant |
| `.madagents/wiki/consultants/`, `.madagents/wiki/lead/` | `/output/.madagents/wiki/…` — the shared wiki |

That table is the Claude Code and opencode layout. A Codex run puts the same content where Codex
looks for it — the lead's slate at `/output/.madagents/memory/lead/MEMORY.md`, each consultant's
inside its own `.codex/agents/<name>.toml` — which is why the two settings below have no Codex
counterpart to pin.

Copying the files in is only half of it — they are *loaded* by Claude Code's auto-memory,
which has to be told about this layout. `madrun setup` pins both halves into the instance's
`.claude/settings.local.json`:

- `autoMemoryEnabled` — mirrors `auto_memory_enabled:` in `madagents/config.yaml`. Written
  explicitly so the run does not inherit the setting from your personal Claude config: a
  `"autoMemoryEnabled": false` there would otherwise mean none of the 46 slates ever load,
  with no sign that anything is wrong.
- `autoMemoryDirectory` — points the lead's slate at `/output/.claude/lead-memory/`. Consultant
  slates are placed by the `memory: project` line on each agent card; the lead has no card, and
  Claude Code's default lives outside the instance and is shared by every run.

Set `auto_memory_enabled: false` in `config.yaml` to turn the whole mechanism off; `madrun.sh`
then says so at setup time, since a seeded pack would sit unread.

## A note on versions

The wiki deliberately caches **lookups, not values**: a page records a
`$MADGRAPH_INSTALL/<file>:<line>` coordinate and the recipe to read it, so a version-dependent number
is re-read from the MadGraph source in front of it rather than recalled. The packs here were
accumulated against **MG5_aMC v3.7.1**; the shipped image now installs **v3.7.2**, so a version skew
between pack and MadGraph is the ordinary case rather than a hypothetical one. Where a coordinate
has moved, that surfaces by design as a lookup which fails to resolve (loud) rather than a stale
number that still reads as valid (silent).
