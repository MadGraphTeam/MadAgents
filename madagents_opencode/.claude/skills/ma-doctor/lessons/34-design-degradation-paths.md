# 34 — Design degradation paths

> After repeated failure, degrade gracefully — ask the user, or spawn a fresh agent — rather than spin in a doom loop.

Agents fall into doom loops and self-confirmation bias: corrected, they re-read their own work,
decide it looks fine, and stop — or keep retrying the same broken approach. The fix is a circuit
breaker: after repeated failure, change strategy rather than loop. A task corrected more than
twice and still wrong goes to a *fresh* agent, not another correction round, and a system that
cannot make progress degrades to asking the human rather than spinning.

**In a harness like this.** When consultants keep failing or contradicting each other, the lead
degrades to asking the user rather than spinning; a sub-question corrected twice and still wrong
goes to a fresh consultant, not more corrections on the stuck one. This pairs with keeping the
human on the loop (lesson 30) — the graceful degradation is often "surface it to the user" — and
with bounding spend (lesson 36), since a doom loop is also a token blowout.

## Where the books say it

- **Src-Analysis** — ch5. The circuit breaker — design degradation paths so that repeated failure degrades gracefully rather than looping.
- **Harness** — §05/§10/§16. The doom loop / self-confirmation bias — corrected >2× and still wrong → a fresh agent, not more corrections; break the loop rather than spin.
