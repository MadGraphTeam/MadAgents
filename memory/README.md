# Memory packs

The agent system in [`madagents/`](../madagents) ships **cold**: the full surface (46 consultant
subagents, 8 skills, the lead's system prompt) but an empty learned tier. A **memory pack** is that
learned tier — what the system accumulated by working on MadGraph tasks — kept separately so you can
choose how much of it a run starts with.

```bash
./madrun.sh                             # interactive: pick the memory from a menu
./madrun.sh --list-memory               # what each option carries, then exit
./madrun.sh --new --memory pretrained   # default: warm, for Anthropic models
./madrun.sh --new --memory pretrained-local   # warm, for a self-hosted model
./madrun.sh --new --memory bare-local   # cold domain, harness know-how only
./madrun.sh --new --memory none         # fully cold
```

## The three packs

| Pack | MadGraph knowledge | Claude Code know-how | For |
| --- | --- | --- | --- |
| [`pretrained`](pretrained) | ✔ 46 slates, 592 wiki pages | ✘ | Anthropic models (Opus, Sonnet) |
| [`pretrained-local`](pretrained-local) | ✔ same | ✔ | a self-hosted / open-weights model |
| [`bare-local`](bare-local) | ✘ | ✔ | a self-hosted model, cold domain |

The two axes are independent, which is what makes the set a matrix rather than a ladder:

- **MadGraph knowledge** — 46 per-consultant slates, a 592-page wiki, and the lead's routing index.
  This is the substance: source-grounded MG5 facts the system worked out and wrote down.
- **Claude Code know-how** — one lead-memory principle on how to wait for a dispatched subagent.
  Frontier Anthropic models already do this correctly, so carrying it costs context and buys
  nothing; a smaller self-hosted model benefits from having it stated. `pretrained-local` is
  exactly `pretrained` plus this principle, and `bare-local` is exactly this principle alone.

The fourth cell — an Anthropic model with no MadGraph knowledge — is the shipped system as-is, so it
needs no pack: that is `--memory none`.

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
accumulated against **MG5_aMC v3.7.1**. Against a different MadGraph version some coordinates will
have moved — by design that surfaces as a lookup that fails to resolve (loud) rather than a stale
number that still reads as valid (silent).
