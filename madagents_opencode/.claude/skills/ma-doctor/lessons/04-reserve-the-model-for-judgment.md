# 04 — Reserve the model for judgment

> Decide with a rule or a check what a rule can decide. Spend the probabilistic model only on what needs taste.

Retrieval and mechanical decisions have correct answers; wrapping them in a probabilistic model
adds cost, latency, and a hallucination surface, not intelligence. A judgment with a definite
mechanical answer is settled by a rule or a shell check, and the model is never consulted.
Because generation is now nearly free, what stays scarce is *judgment* — knowing which plan is
right, which output is wrong at the root — so the model's budget belongs there.

## In a harness like this

Before a dispatch, ask "is this decidable by a check?" — is the tool installed, what version, does
this path exist (a `which` / `ls` / read-the-version-file check, not a consultant); did the run
produce output (the file exists, not a model asked "did it work"). This saves tokens and removes a
hallucination surface at once, and reserves the model — and the consultant roster — for genuine
domain judgment. When auditing a harness, flag any agent or step that spends a model call on a
question a deterministic check would answer for certain.

## Where the books say it

- **Hermes** — §08 (do not model a deterministic lookup — fetch the real bytes), §05/§19 (the Curator's pure-function state machine advances on timestamps with no model: separate what a rule can decide for certain from what needs judgment).
- **Loop** — §08. The loop makes generation almost free, so the scarce good becomes judgment — knowing which plan is right, and which output runs fine while being wrong at the root.
