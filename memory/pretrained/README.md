# `pretrained` — MadGraph knowledge, for Anthropic models

The accumulated learned tier of the MadAgents system: what it worked out about MG5_aMC while
solving MadGraph tasks, written down in the form it reads back.

```bash
./madrun.sh --new --memory pretrained
```

This is the default pack. Use it when the session runs on an Anthropic model (Opus, Sonnet) — i.e.
the ordinary `claude` CLI on a Claude subscription or API credits.

## Contents

| Tree | What it holds |
| --- | --- |
| `.claude/agent-memory/<agent>/MEMORY.md` | **46 consultant slates** — one per specialist subagent: the slice it owns, its standing cautions, and pointers into the wiki. |
| `.claude/lead-memory/MEMORY.md` | The lead's slate: its role, standing domain notes, the FIFO of recent lessons, the **wiki page index** it sweeps every task against, and its deliberate-lookup pages. |
| `.claude/lead-memory/*.md` | **4 lead playbooks** on cross-slice seams — multi-level decay parentheses, the SMEFT `NP` convention lookup, sub-threshold `bwcutoff`, and unit-conversion discipline. |
| `.madagents/wiki/consultants/`, `.madagents/wiki/lead/` | **592 wiki pages** — the shared, source-grounded knowledge base. |

## What is *not* in it

Nothing about operating Claude Code. The system's one harness principle — how to wait for a
dispatched subagent rather than polling for it — is deliberately absent here: an Anthropic model
already handles background subagents correctly, so stating it only spends context. If you point the
session at a self-hosted model, use [`pretrained-local`](../pretrained-local) instead, which is this
pack plus that principle.

## Provenance, stated plainly

- The learned tier was accumulated across training runs of the agent system on MadGraph tasks, then
  carried forward across successive versions of the system's surface.
- Not all of it was earned by an agent. The lead's **routing index** — the entries it sweeps a task
  against — was re-keyed by hand so that each entry is matched by *the physics regime a task
  implies* rather than by source-file names a reader would have to already know. It was authored
  from the wiki pages and slates below it, and from MadGraph source.
- The lead's slate was also pruned of content that merely restated its own system prompt, which it
  loads every turn regardless; what remains is what it actually learned.
- None of this content was derived from any held-out evaluation set.

## Extending it

The pack is fixed. `madrun.sh` copies it into the run instance, and the session reads and writes
that copy — see [`../README.md`](../README.md).
