# 35 — Constraints, not model size, are the edge

> Reliability comes from the quality of the scaffold, not the size of the model. So invest in the substrate — and pre-build the competence a weak model can't improvise cold.

The headline result: a team merging 1,300+ PRs a week runs on a *fork of an open-source tool*,
not a stronger model: reliability comes from the quality of the constraints rather than the size
of the model, and the main reason it works has almost nothing to do with the model. AI amplifies
the engineering it sits on; good human infrastructure is good AI infrastructure. The corollary for
weak models: a design that leans on the agent *deriving* its competence cold at runtime demands a
strong model to do the deriving — so for a weak model the competence must be pre-built and carried,
not improvised.

**In a harness like this.** The system beats a bare assistant on the *same* model; the edge comes
from the scaffold — source-grounding, the reviewer roster, the calibration discipline, and above
all the filled-in memory and wiki — not a better model. Cold orchestration alone is a weak deal
against a bare baseline; the value lands once the memory and wiki have filled in (lesson 24, the
compiled knowledge), so the form worth shipping is one that already carries that state. This
carries straight to the future-vision: a strong scaffold is what lets a weaker local or
open-source model perform — the competence must be pre-built and frozen into the carried state,
not re-derived per session. The carried state is the portable performance. The stable-source lens
reinforces it: MadGraph internals are static and finite, so that competence can be pre-walked once
and frozen.

## Where the books say it

- **Loop** — §06. Stripe Minions on a Goose fork: reliability comes from the quality of the constraints rather than the size of the model — the grounding for "every scaffold earns its keep."
- **Harness** — §09. Good human infrastructure is good AI infrastructure; the substrate (doc corpus, wiki, plumbing) is what makes it work, more than model choice.
- **Polymarket** — §07. The scaffold amplifies the underlying method — a flawed strategy executed faster just loses faster (lesson 08's twin).
- **OpenClaw** — §09. Avoiding external pre-built tools costs you model capability — the agent has to be stronger — so for a weak model, pre-build and carry the competence.
- **CC-Guide** — §10. The three-layer model: invest in Context + Harness (compounding / exponential), not the Prompt (one-time).
