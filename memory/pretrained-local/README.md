# `pretrained-local` — MadGraph knowledge + harness know-how, for self-hosted models

[`pretrained`](../pretrained) plus one principle on operating Claude Code itself.

```bash
./madrun.sh --new --memory pretrained-local
```

Use it when the session runs on a **self-hosted / open-weights model** rather than an Anthropic one.

Which model a run talks to is settled before the session starts and is not part of this pack: a
memory pack only decides what the agent *knows* on the way in.

## Contents

Identical to [`pretrained`](../pretrained) — 46 consultant slates, 592 wiki pages, the lead's
routing index — with two additions:

| Tree | What it adds |
| --- | --- |
| `.claude/lead-memory/MEMORY.md` → `## Core operating principles` | A first-person statement of how the lead waits for a dispatched subagent: end the turn, no tool call, and the harness re-invokes with the complete result. So: never poll, never sleep, never re-dispatch to ask whether it is done, never read the agent's transcript file. |
| `.claude/lead-memory/subagent-patience.md` | The same discipline as a lead playbook page. |

That is the whole difference. `diff -r` against `../pretrained` shows exactly these two things.

## Why it is a separate pack

A frontier Anthropic model gets subagent dispatch right without being told, so for it this content
is pure context cost. A smaller self-hosted model is much likelier to poll, to act on a partial
return, or to try to read a subagent's output file — each of which produces a worse answer than
simply waiting. Stating the mechanic in the lead's own memory, in the first person, is cheap
insurance there.

If you want to measure what the MadGraph knowledge itself is worth on a local model, the controlled
comparison is this pack against [`bare-local`](../bare-local): the two are identical except that
`bare-local` has no MadGraph knowledge at all.

## Provenance

Same as [`pretrained`](../pretrained) — see its README. The added principle is hand-kept operating
guidance, not something an agent discovered.

## Extending it

The pack is fixed. `madrun.sh` copies it into the run instance, and the session reads and writes
that copy — see [`../README.md`](../README.md).
