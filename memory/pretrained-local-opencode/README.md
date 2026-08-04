# `pretrained-local-opencode` — MadGraph knowledge + harness know-how, for self-hosted models

[`pretrained`](../pretrained) plus one principle on operating opencode itself.

```bash
./local/madrun.sh --new --provider opencode --memory pretrained-local-opencode
```

Use it when the session runs on a **self-hosted / open-weights model** rather than an Anthropic one.

Which model a run talks to is settled before the session starts and is not part of this pack: a
memory pack only decides what the agent *knows* on the way in.

## Contents

Identical to [`pretrained`](../pretrained) — 46 consultant slates, 592 wiki pages, the lead's
routing index — with two additions:

| Tree | What it adds |
| --- | --- |
| `.claude/lead-memory/MEMORY.md` → `## Core operating principles` | A first-person statement of how dispatch actually returns here: a consultant's complete reply is the result of the `task` call itself, in the same turn. So: never end the turn expecting to be re-invoked, never poll or sleep, never re-dispatch to ask whether it is done, never hunt for a notification or the agent's transcript — and put everything the consultant needs into the call, because a subagent cannot ask anything back. |
| `.claude/lead-memory/subagent-dispatch.md` | The same discipline as a lead playbook page. |

That is the whole difference. `diff -r` against `../pretrained` shows exactly these two things.

## Why it is a separate pack

A frontier Anthropic model gets subagent dispatch right without being told, so for it this content
is pure context cost. A smaller self-hosted model is much likelier to poll, to act on a partial
return, or to try to read a subagent's output file — each of which produces a worse answer than
simply waiting. Stating the mechanic in the lead's own memory, in the first person, is cheap
insurance there.

If you want to measure what the MadGraph knowledge itself is worth on a local model, the controlled
comparison is this pack against [`bare-local-opencode`](../bare-local-opencode): the two are identical except that
`bare-local-opencode` has no MadGraph knowledge at all.

## Provenance

Same as [`pretrained`](../pretrained) — see its README. The added principle is hand-kept operating
guidance, not something an agent discovered.

## Extending it

The pack is fixed. `madrun.sh` copies it into the run instance, and the session reads and writes
that copy — see [`../README.md`](../README.md).
