# 17 — The lead owns the final voice

> Consultant returns are internal, concise, labeled signal. The lead synthesizes its own answer and never relays raw text.

A delegate returns a short summary — the signal, ~1-2k tokens — not its full exploration; the
isolated context keeps the lead's window clean (lesson 13). Every message the lead sends is to
the user, so it synthesizes the signal into its own voice rather than forwarding raw worker text.
And the return should carry its trust as a structured property — "is there a real source?" baked
into the value — so the lead knows what to rely on.

**In a harness like this.** Consultant returns are internal signals; the lead synthesizes them
into its own answer and never relays raw consultant text. The return is *labeled* (DIRECT /
INFERRED / HYPOTHESIS) so the lead can weigh it — the confidence labels are this principle made
structural (pairs with lesson 03). A consultant's full source-walk stays in its own context; the
lead gets the compressed, labeled verdict.

## Where the books say it

- **Claude Code Source-Code Analysis** — ch9. The lead owns the final voice — every message that leaves the system is addressed to the user; consultant returns are internal, never relayed raw.
- **Harness Engineering** — §04/§08. Concise consultant returns — a 1,000-2,000-token summary, never dumping the exploration into the main context.
- **OpenClaw: The Complete Guide** — §09. A side-quest rolls back carrying only a one-line summary — return frugality.
- **Hermes Agent** — §11. Mark ungrounded returns explicitly (`degraded=true`) — bake "is there a real source?" into the return value.
