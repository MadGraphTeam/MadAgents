# 19 — Guardrails by exclusion

> Stating what does NOT exist / what NOT to do steers the model and saves more context than enumerating what does — but always pair a prohibition with its escape route.

Excluding the model's plausible-but-wrong defaults is the cheap, high-leverage move: a single
grounded "this does not exist / don't do X" fences off a whole branch of confident-but-wrong
behavior, and decreasing the solution-space flexibility increases trust. The test of a card is
how much "what not to do" it carries — the negative list, the pitfalls, the when-not-to-use, and
where to route instead. One caveat: never leave a bare "never do X" — give the alternative ("use
Y instead"), or the agent that concludes it must do X gets stuck.

**In a harness like this.** A single grounded exclusion line in a card or rule fences off a whole
branch of confident-wrong MadGraph behavior ("MadGraph does NOT support X, use Y"; "this install
has no Z, do not call it"), and a card that names its own boundary and routes elsewhere prevents
a class of mis-dispatch. Caveat: the exclusion must be *true and grounded* in the source
(version-stamped if version-specific) — a wrong exclusion blocks a valid path. Safe on a fresh
system: a grounded exclusion *prevents* first-use failures rather than risking them.

## Where the books say it

- **Harness Engineering** — §06/§14/§15. Guardrails by exclusion — declare what does not exist; narrowing the solution space increases trust (Boeckeler); cf. Ghostty's note that a given package carries no unit tests.
- **Claude Code: The Complete Guide** — §05/App G. Pair a prohibition with its alternative rather than leaving a bare never; documented gotchas beat best-practice filler.
- **Hermes Agent** — §10. A good skill states when *not* to use it — the negative list, the pitfalls and the when-not-to-use-me section are what turn a document from looking correct into actually running correctly.
