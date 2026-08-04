---
name: subagent-dispatch
description: The task tool hands back a subagent's complete reply as its own result; there is nothing to wait for, and nothing to ask it afterwards.
metadata: 
  node_type: memory
  type: user
---

**A dispatched consultant's full reply comes back as the result of the `task` call itself.**

There is no waiting mechanic here, because there is nothing to wait for. You call `task`, the
consultant runs, and its complete answer is the value that call returns to you — in the same turn,
before you write anything. So:

- Do **not** end your turn expecting to be re-invoked with the result. Nothing will re-invoke you;
  you will simply have stopped, and the work will be lost.
- Do **not** poll, `sleep`, or dispatch the same consultant again to ask whether it is finished.
- Do **not** go looking for a status channel, a completion notification, or the consultant's own
  transcript. None of those exist here.

**Put everything the consultant needs into the dispatch.** It starts in a fresh context with no
sight of your conversation, and it **cannot ask you anything** — the question tool is denied to
subagents, so a dispatch that depends on a follow-up question comes back useless. State the task,
the inputs, and what "done" looks like, in the call itself.

**Then answer from its full reply, not from part of it.** Acting on a partial return produces a
worse answer than reading what actually came back. If a consultant returns *nothing at all* — an
empty reply rather than an error — do not invent what it might have said: report that it returned
empty, and dispatch again with a smaller, sharper task.
