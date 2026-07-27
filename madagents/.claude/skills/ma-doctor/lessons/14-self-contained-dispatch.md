# 14 — Self-contained dispatch

> A consultant sees only what you hand it — never the lead↔user conversation. Every brief must carry its own context.

A worker cannot see the conversation between the coordinator and the user; what it cannot see
does not exist for it. So every dispatch must be self-contained: the full sub-question, the
user's verbatim ask, the relevant paths, and what "done" looks like. The goal is the minimum set
of high-signal tokens that maximizes the probability of the desired outcome — complete, not
bloated.

## In a harness like this

A consultant works in a clean, independent context window (lesson 13) and sees only the brief, so
the brief carries the full sub-question, the user's verbatim ask, and the paths. Here the cost of
an underspecified brief is milder than the books' worst case: re-dispatch is designed in, so an
underspecified brief costs a recoverable round-trip, not a cold failure — but a self-contained
brief avoids the wasted re-dispatch.

## Where the books say it

- **Src-Analysis** — ch9. Workers cannot see the conversation between coordinator and user, so every prompt must be self-contained.
- **Harness** — §06/§16. What the agent cannot see does not exist for it; aim for the minimum set of high-signal tokens per dispatch.
- **Codex** — §07/App C. A delegated brief is self-contained because the context is fresh — the firm basis is that subagents get independent context, and here it is recoverable by re-dispatch (milder than a cloud task that genuinely cannot ask back).
- **CC-Guide** — §08. Subagents = independent context — the structural reason a brief must stand alone.
