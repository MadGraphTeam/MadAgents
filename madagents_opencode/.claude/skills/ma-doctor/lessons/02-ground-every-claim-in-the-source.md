# 02 — Ground every claim in the source

> Answer from the source, not from recall. What the agent can't see doesn't exist; the source is the only ground truth.

The fix for confident wrongness (lesson 01): ground every factual, version-sensitive, or data
claim in an external source rather than in recall. Read the raw source and understand it (grep
over RAG — precise, zero-maintenance, always-latest); when the answer is in the source
verbatim, fetch the real bytes rather than have a model recite them. A recalled memory is a
*lead to verify*, not truth.

## In a harness like this

Source-as-only-truth is the discipline behind the whole roster: consultants source-walk the
internals and cite file:line; the lead routes the *question* to a source-grounded specialist
rather than pre-deciding the answer. Stable-source lens: the source is released, versioned, and
byte-static, so a recorded location stays valid within a version and grounding is reliably
durable. The one residual is a version bump — guarded structurally, by caching the lookup rather
than the value: a stale coordinate fails to resolve and announces itself. When auditing a
harness, check that every fact-producing agent is pointed at a real source and cites it, and that
memory is treated as a lead to re-confirm rather than as established truth.

## Where the books say it

- **Src-Analysis** — ch8 (grep beats RAG — search the source rather than relying on recall), ch6 (treat memory as a lead rather than as truth; remember preferences, forget code).
- **Harness** — §06/§16. What the agent cannot see does not exist for it; the repo is the single source of truth; aim for the minimum set of high-signal tokens per dispatch.
- **CC-Guide** — §06. Describe symptoms rather than diagnosing causes — hand the question to the source-grounded agent and let its read of the reliable source beat a presupposed answer.
- **Codex** — §10. A coding agent that reads before it edits outperforms a stronger model running on unstable defaults — read-before-act over clever recall.
- **Hermes** — §08. Deleted an LLM summarizer that fabricated passages and was thousands of times slower than returning the real rows; when the answer is in the source, fetch it.
- **Obsidian** — §05 P6 / §06. The raw tier is the source of truth, append-only and never modified; AI-derived knowledge can hallucinate, so source and derived get different trust and handling.
- **Polymarket** — §01/§03. Pooling does not manufacture information — the structure only aggregates what participants actually know; ungrounded aggregation is the sealed-conclave failure (a near-zero price on the actual winner).
