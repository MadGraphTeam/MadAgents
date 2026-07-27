---
description: About to say what a mechanism, default, or branch does, on the evidence that the code exists rather than that it runs.
---

# Dead-code / liveness — verify reach before describing

## When it applies
Any question that turns on **what a named mechanism, default, function, or branch does** — especially when the answer is being inferred from the code's *presence* rather than its *reachability*. Surface cues: "what does function X compute", "what's the default of Y", "does branch Z fire", "MadGraph adapts/uses/computes …" (a pretrained generality about MadGraph's behaviour). The trap is uniform: **in this codebase, a present-and-readable code path is frequently unreachable at runtime, and a compiled-in default frequently diverges from the operative one.** Reasoning from presence is the single most recurrent cross-slice error mode the wiki has found.

## Dispatch discipline (the lead-level content)
There is **no single MadGraph mechanism** to cite here — the dead-ness *modes* differ per instance (taxonomy below), so consultants who tried to write one within-subtree "dead code" page correctly found it *not supportable* (phase-space, numerical, ufo all reached this conclusion). What generalises is the **dispatch behaviour**, which is lead-owned:

1. When the question turns on mechanism/value/branch X, **add to the dispatch an explicit reach-check instruction**: *"Before describing X, confirm X is actually reached at runtime for THIS input — grep for live callers, check the enclosing guard, confirm the compiled-in default isn't overridden. Presence ≠ liveness."*
2. **Prefer the consumer's own predicate over a convenience grep.** The canonical failure: a literal `grep "perturbative_expansion = 1"` missed the `loop_qcd_qed_sm` `= 99` model; the importer's own test is `> 0`. When a count or membership depends on a source test, make the consultant run the *source's* predicate, never a literal-value grep. (See routing pages nlo-model line.)
3. **Treat a "the function exists, so it does Z" claim in a consultant return as INFERRED, not DIRECT** — until the return shows a live caller / firing guard. A returned mechanism description with no reachability evidence is exactly the claim this playbook exists to catch.

## Dead-ness mode taxonomy (so the reach-check is specific)
Naming the mode makes the consultant's reach-check sharp. Observed modes:
- **No caller** — `def` exists, grep finds no production call site (chain-decay/madwidth AbstractModel cluster = test-only; phase-space `boost_to_frame`/`ungen_s`; madspin `generate_all_matrix_element`; rivet `run_plot_delphes`).
- **Guarded-out** — a branch behind `if(.true.)` / always-false / always-true that fences off the live body (phase-space `psect` Pittau-alpha adaptation; ufo dead `add_coupling`).
- **Compiled-in default diverges from operative** — a `DefaultParam()`/hardcoded constant that is never the value actually used (madloop `MadLoopParamReader.f`; param-card ParamCardRule category loaded-but-never-enforced).
- **Reachable only via a non-default entry** — live through the Python API but errors in the REPL, or vice versa (madloop `--diagram_filter`: silent no-op via API, but `InvalidCmd "No particle --diagram_filter"` in the REPL because the bracket path bypasses the strip).
- **Dead-write / typo-shadowed** — an attribute written under one spelling, read under another (numerical `self.gran` vs `ngran`; `self.onefail` vs `oneFail`).
- **Convenience-predicate miss** — the count/membership is right but the *scan* used to derive it is wrong (nlo-model `=1` grep missing `=99`).
- **False-dead / disjoint-coverage-misread-as-shadowing** (the costly INVERSE — *looks dead but is LIVE*) — guard A is marked DEAD/SHADOWED because "earlier guard B catches the same syntax," but A and B match **disjoint input forms**, so A is live for its own form. Instance: nlo-syntax single-`$` at NLO — `check_add:129` (B1, `'$' in args`, spaced `$ g`) vs `do_add:476` (B2, `re.search(\b\$\b)`, glued `d$g`); the "B1 shadows B2 → B2 dead" reasoning was probe-disproven (`d$g` reaches B2). The other six modes are "looks live, is dead"; this one inverts. **Discipline: before marking any guard SHADOWED by a sibling on the "same syntax," probe the EXACT input-form each predicate matches — reasoning alone ("the other catches it first") is insufficient; a marked-dead guard that is actually reachable is the costliest direction (it makes you describe the wrong user-visible error).**

## Anticipated trap
The biggest mis-route: shipping a consultant's mechanism description as a confident answer when the consultant described *what the code would do if it ran* without establishing that it runs. Reconcile by re-reading the return for a live-caller / firing-guard citation; if absent, re-dispatch with the reach-check instruction naming the suspected mode.

## Instance pointers (consultant-owned; do not restate their facts here)
Each lives on the owning consultant's dead-code page; the routing pages "Vestigial / dead-code-with-divergent-defaults" seam carries the full enumerated list with file:line. This playbook is the *dispatch* layer above that seam — the seam catalogs instances, this page says how to dispatch so you don't add to it.

## Return-interpretation hint
A consultant return that says "investigated, not supportable as a generalization page" for its *own* dead-code cluster is **correct and expected** — the modes genuinely differ within a slice. That non-write is not a gap; the generalization lives here at the dispatch layer, not in the consultant subtree.
