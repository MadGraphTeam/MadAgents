# 12 — Do not over-fan-out

> A few clean, independent slices beat a large noisy crowd. Over-fanning costs tokens *and* dilutes the answer.

Fanning out has real overhead (split, distribute context, merge) and pays only when the task is
large enough *and* the slices are genuinely independent — "draw a dependency graph first; only
tasks with no connecting arrows can run in parallel." Beyond cost, more participants is not
automatically more signal: when their outputs conflict, averaging them dilutes the best idea
(following all of them amounts to following none). The cleaner each slice is cut, the easier the
later verification and the easier to pin down which one went wrong.

## In a harness like this

The lead should not fan out consultants for a small question, and the slices it does fan out must
not depend on each other's output. Over-fan-out is a *quality* cost as well as a token cost —
routing to too many consultants on one question makes the lead average noise. The right move is
to route to the few correct specialists, not to poll everyone. (How aggressively to cap fan-out
is a design decision.)

## Where the books say it

- **Skills** — ch9. A half-hour sequential task can take longer once you spend twenty minutes splitting it and ten merging it back; draw the dependency graph first.
- **CC-Guide** — §08. N agents ≈ N× tokens; parallelize only when splittable + merge-cheap (the six-agent afternoon that runs up a big bill).
- **Polymarket** — §05/§09. Copying fifteen wallets dilutes the best ideas until following all of them amounts to following none — stick to three to five; a low participant cap beats high volume because it keeps speculative behaviour from swamping the signal.
- **Loop** — §03/§04. Clean cuts before dispatch — the cleaner the tasks are cut, the easier verification and merging become later, and the easier it is to pin down which one went wrong.
- **Hermes** — §11. Don't add machinery (an extra dispatch/routing layer) that costs more than it saves.
