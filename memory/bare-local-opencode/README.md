# `bare-local-opencode` — harness know-how only, for self-hosted models on opencode

No MadGraph knowledge at all: an empty learned tier, plus the single principle on how to operate
**opencode** that [`pretrained-local-opencode`](../pretrained-local-opencode) adds to
[`pretrained`](../pretrained).

```bash
./local/madrun.sh --new --provider opencode --memory bare-local-opencode
```

Use it when the session runs on a **self-hosted / open-weights model** and you want the system to
work the MadGraph problem out for itself — while still getting subagent dispatch right.

Which model a run talks to is settled before the session starts: a memory pack chooses what the
agent knows, never which model it runs on.

## Not interchangeable with the `-cc` packs

[`bare-local-cc`](../bare-local-cc) carries the *Claude Code* dispatch mechanic — end the turn with
no tool call, and the harness re-invokes you with a `<task-notification>` carrying the result. On
opencode that mechanic does not exist, and the instruction is worse than useless: a lead that ends
its turn waiting to be re-invoked has simply stopped, and the dispatched work is lost.

opencode returns a consultant's complete reply as the result of the `task` call itself, in the same
turn. That is what this pack states instead. Pick the pack that matches the CLI the run is built
for; they are the same pack in every other respect.

## Contents

| Tree | What it holds |
| --- | --- |
| `.claude/lead-memory/MEMORY.md` | One section, `## Core operating principles`, with one bullet: a dispatched consultant's full reply comes back as the `task` call's own result — so no waiting, no polling, no re-dispatching to ask, and everything the consultant needs goes into the call, because a subagent cannot ask anything back. Byte-identical to the bullet `pretrained-local-opencode` carries. |

That is the entire pack. There are no consultant slates and no wiki pages; the consultants start
with empty memory and the wiki is created as the session writes to it.

## Why this exists rather than `--memory none`

A fully cold run (`--memory none`) starts with a zero-byte lead slate — including no statement of
how dispatch returns. On a self-hosted model that tends to show up as polling, as re-dispatching a
consultant to ask whether it has finished, or as acting on a partial return; the failure looks like
a domain mistake but is really a harness mistake, which muddies any comparison you are trying to
make.

So this pack is the honest cold arm for a local model: **identical to
[`pretrained-local-opencode`](../pretrained-local-opencode) in everything except the MadGraph
knowledge**. Run the two against each other and the only variable is what the system knows about
MG5_aMC.

## Extending it

The pack is fixed. `local/madrun.sh` copies it into the run instance, and the session reads and
writes that copy — so a run started here accumulates its own slates and wiki pages in the instance,
and forking that run (`./local/madrun.sh` → `f`) carries them forward. See
[`../README.md`](../README.md).
