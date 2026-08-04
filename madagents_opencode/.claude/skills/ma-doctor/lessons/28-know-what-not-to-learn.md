# 28 — Know what not to learn

> Never harden a transient or environment-specific failure — or a negative tool claim — into durable memory. Distill the non-obvious; don't transcribe the surface.

The aggressive capture bias (lesson 27) is only safe because it is paired with a brake: a
do-not-learn blacklist. A wrong negative claim ("tool X is broken", "MadGraph can't do Y")
hardens into a refusal the agent cites against itself for months after the cause is fixed. The
criterion before any durable write: *would this rule still hold on a different install, machine,
or version?* Distinguish a real mistake (got the arguments wrong — learn it) from an environment
glitch (this machine lacks a binary — don't). And capture what was unexpected or non-obvious, not
the surface — the store is not a notebook.

## In a harness like this

This is the guard that keeps the accumulated memory and wiki from collecting poison. It intersects
the byte-static-source consideration — a transient install or environment failure must not become a
durable MadGraph fact — and the confidence labels (a negative claim from one failed run is exactly
the unreliable-recall failure the system designs around). It is the brake that lets the capture
bias (lesson 27) dare to be active. When auditing the learn loop, look for the blacklist: a capture
discipline with no do-not-learn criterion in front of it will, over time, harden environment
glitches and one-off negative claims into standing refusals.

## Where the books say it

- **Hermes** — §06. The do-not-learn blacklist: negative claims about tools harden into refusals the agent cites against itself for months; the criterion is whether the claim would hold on a different install, machine or version; env-dependent failures, negative tool claims, one-off task debris.
- **Src-Analysis** — ch6. Distill, don't transcribe — capture what was unexpected or non-obvious rather than the surface; the store is not a notebook.
