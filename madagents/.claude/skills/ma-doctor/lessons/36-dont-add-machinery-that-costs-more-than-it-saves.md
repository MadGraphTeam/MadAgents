# 36 — Don't add machinery that costs more than it saves

> A mechanism added to save context must not become a larger burden itself. Confirm the overhead is smaller than the saving — and bound runaway spend.

Before adding a routing layer, a lazy-load, or an extra dispatch, confirm its overhead is smaller
than what it saves (one system idles its on-demand tool-search whenever the deferrable tools fall
below a set fraction of context — the saving has to clear a threshold). Fan-out is the canonical
example: the split/merge overhead can exceed the work saved. And an autonomous mechanism needs hard
caps before it ships — a per-run budget and max retries — so one idle-spinning bug can't burn a
whole night's quota.

**In a harness like this.** Before adding scaffolding, confirm the overhead is repaid — pairs with
match-complexity (lesson 11). When the saving cannot be measured empirically, prefer not adding the
machinery at all rather than adding it and hoping it pays off. Avoid unbounded self-dispatch or
reviewer cascades that could spiral; the brake on a doom loop (lesson 34) is also a spend brake.

## Where the books say it

- **Hermes** — §11. The mechanism that saves context must not become a burden itself — Hermes idles its tool-search when the deferrable tools fall below a small fraction of context.
- **Skills** — ch9. Don't over-parallelize — the split/distribute/merge overhead can exceed the work saved.
- **Loop** — §07. Bound runaway token spend — set hard caps before shipping (per-run budget, max retries) so an idle-spinning bug cannot burn through a whole night's quota.
