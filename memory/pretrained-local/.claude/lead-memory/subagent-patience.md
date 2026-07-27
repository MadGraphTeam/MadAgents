---
name: subagent-patience
description: Wait for complete subagent returns before acting; the harness resumes you automatically at zero token cost.
metadata: 
  node_type: memory
  type: user
---

**Be patient with dispatched subagents — wait for the COMPLETE reply before you act.**

When you dispatch a consultant or subagent, the harness resumes you automatically when it returns:
- **Foreground dispatch:** suspends your turn at zero token cost until the result arrives.
- **Background dispatch:** sends a completion notification and re-invokes you when the subagent finishes.

In either case, you do NOT need to poll, spin in a wait loop, or proceed on partial or early output. Dispatch, let the subagent finish, and answer from its FULL reply.

Answering before a consultant returns — or from an incomplete return — produces worse answers than simply waiting. Impatience is a defect; patience is free.