# `bare-local` — harness know-how only, for self-hosted models

No MadGraph knowledge at all: an empty learned tier, plus the single principle on how to operate
Claude Code that [`pretrained-local`](../pretrained-local) adds to
[`pretrained`](../pretrained).

```bash
./madrun.sh --new --memory bare-local
```

Use it when the session runs on a **self-hosted / open-weights model** and you want the system to
work the MadGraph problem out for itself — while still getting subagent dispatch right.

Which model a run talks to is settled before the session starts: a memory pack chooses what the
agent knows, never which model it runs on.

## Contents

| Tree | What it holds |
| --- | --- |
| `.claude/lead-memory/MEMORY.md` | One section, `## Core operating principles`, with one bullet: how the lead waits for a dispatched subagent — end the turn, no tool call, and the harness re-invokes with the complete result. Byte-identical to the bullet `pretrained-local` carries. |

That is the entire pack. There are no consultant slates and no wiki pages; the consultants start
with empty memory and the wiki is created as the session writes to it.

## Why this exists rather than `--memory none`

A fully cold run (`--memory none`) starts with a zero-byte lead slate — including no statement of
the wait mechanic. On a self-hosted model that tends to show up as polling, as acting on a partial
subagent return, or as an attempt to read a subagent's transcript file; the failure looks like a
domain mistake but is really a harness mistake, which muddies any comparison you are trying to make.

So this pack is the honest cold arm for a local model: **identical to
[`pretrained-local`](../pretrained-local) in everything except the MadGraph knowledge**. Run the two
against each other and the only variable is what the system knows about MG5_aMC.

## Extending it

The pack is fixed. `madrun.sh` copies it into the run instance, and the session reads and writes
that copy — so a run started here accumulates its own slates and wiki pages in the instance, and
forking that run (`./madrun.sh` → `f`) carries them forward. See [`../README.md`](../README.md).
