---
description: MG5 said no. A parse or validation rejection, or a failed correctness/stability check, and which guard fired.
---

# Process verification — multi-slice fan-out

"Verify / check / validate my process", "what does `check` do", "why was my (BSM/NLO) process rejected at generate/add", "is my loop numerically stable", "is the amplitude gauge-invariant" — all fan across the slices below. Route the *sub-question* to the owning slice; do not answer "the check passed/failed" yourself. Dispatch behaviour only; confirm one cited file:line before adopting a consultant page as evidence.

**Complement:** this page routes the *loud* failures — MG5 says no (rejection) or a runtime/identity check fails. For the *silent* counterpart — MG5 accepts, runs clean, gives a σ, but the **amplitude scope ≠ user intent** (single-`$` keeps the diagram, a chain clause distributes to all parents, a comma-only sub-decay is discarded, the inclusive ME ≠ the resonant chain with the same final state) — see `process-line-scope-traps.md`. When a user reports a *wrong result* rather than a *rejection*, suspect the silent class first.

There are **two distinct kinds of "verification"**, and they live in different slices:
- **Acceptance verification** — does the process spec parse / generate / pass MadGraph's structural guards (parse-time + add-time + loop-capability)?
- **Correctness verification** — does the *generated amplitude* satisfy physics identities (gauge / Lorentz / Ward / permutation / CMS) or stay numerically stable at runtime?

## Sub-question → owner

- **The explicit `check` command** (`do_check` → `process_checks.py`; sub-checks `gauge`/`lorentz`/`permutation`/`brs`/`cms`/`process` + loop-only `stability`/`timing`/`profile`) → **process-syntax** `check-validators-verification-map.md` (semantics, tolerances, report columns, tree-vs-loop availability) + `check-command-validators.md` (parse / arg-entry). **TRAP (by pointer, do not restate the mechanism): the sub-check NAMES are counter-intuitive** — `brs` tests the **Ward/BRS identity** (needs a massless spin-1 present or it self-skips), `gauge` compares **unitary↔Feynman |M|²**. `full` = `gauge`+`permutation`+`lorentz`+`brs` only (NOT `cms`, NOT the loop-only checks). Every sub-check runs a real ME evaluation (compile+run), so a `check` on a loop process is a MadLoop run.

- **Parse-time rejection on `generate`/`add` ("why did my process line raise")** → **nlo-syntax** `nlo-parse-guard-firing-order.md` — the ordered LIVE-vs-SHADOWED/DEAD guard catalog along Switcher → `check_add` → `do_add` → `extract_process`. Several guards are DEAD (shadowed by an earlier outer one); route the "what message fires" question here, not to the slice of the logically-owning inner guard.

- **Order-constraint rejection** (an order the model doesn't declare; squared-order/auto-order issues) → **coupling-order** `two-layer-order-validation.md` (parse-time `InvalidCmd` Layer A vs post-build `MadGraph5Error` Layer B) + `smeft-np-power-counting.md` for NP/DIM6/FCNC. The **rejected-order valid-set message is built from a Python `set` → prefix order is non-deterministic per-launch; never quote a fixed order** (see coupling-order-nlo-bracket-seams.md).

- **NLO add-time structural re-validation** (re-checks the LO parser never ran) → **amcatnlo** `proc-validity-nlo-revalidation-hook.md` — `proc_validity()` at `amcatnlo_interface.py:527`: initial-state-count mismatch across `add process` lines, decay-chain-with-loops reject, perturbed-decay reject (a second net), difficulty warning, v3.1-syntax ambiguity Exception. **TRAP (dead-code-liveness instance): the real-model / loop-capability re-check is nlo-model's `validate_model` + `proc_validity` in `loop_interface.py`; its `if not 'real':` branch is DEAD (`loop_interface.py:257`, always False), so the loop-adequacy + Feynman-gauge checks under it never run via that path. `amcatnlo_interface.py:513` is only the CALL site of `validate_model` — the def + dead-branch detail live in nlo-model (`process-loop-capability-gates.md`); route there and don't pin the def line (consultant source-walks disagree on the exact line — the consultant page is authoritative).**

- **Loop numerical-stability verification at RUNTIME** (event-generation time, NOT generation time) → **madloop** `loop-matrix-runtime-driver.md` — the H/T/U `RET_CODE`, `##W03` unstable-point dumps (NEPS-gated → log undercounts EPS), pole-cancellation + JAMP self-consistency cross-checks. This is what MadLoop reports per phase-space point, distinct from the `check stability` command which samples points up-front.

- **Loop-capability rejection** (`[QED]`/`[QCD QED]` on a QCD-only loop model; `[…]` on a tree-only model) → **eft** `eft-model-loop-capability.md` (the user-visible gate `loop_interface.py:355-356` SHADOWS the deeper `madgraph_interface.py:5286` "not among the perturbation orders" guard) + **nlo-model** `process-loop-capability-gates.md` (CheckLoop earliest gate; `perturbative_expansion>0` predicate — run the live `>0` scan, never quote a loop-model count, see nlo-fanout.md).

## Central theme — shadowing (route to the OUTER guard's slice)

A recurring shape across this fan-out: a verification REJECTION the user sees is raised by an **outer/earlier guard** that shadows a deeper inner guard (often itself DEAD). Confirmed shadowing instances: perturbed-decay (Switcher interface-switch → amcatnlo/loop_interface, the cmd-layer + enumeration guards both dead), loop-capability `[QED]` (loop_interface `:356` gate shadows the deep `extract_process` `madgraph_interface.py:5286` guard), proc_validity dead `if not 'real':` (nlo-model, `loop_interface.py:257` — NOT amcatnlo's `:527` proc_validity). **NOT a shadowing instance: single-`$` at NLO** — `check_add:129` (B1, `'$' in args`, spaced `$ g`) and `do_add:476` (B2, `re.search(\b\$\b)`, glued `d$g`) cover **disjoint input forms**, so neither is dead; B2 is LIVE for the glued form. Marking B2 "shadowed by B1" was a reach-check error — probe each guard's exact matched input-form before declaring one dead (see dead-code-liveness.md). **Consequence for routing: "which error message fires for input X" is owned by the slice of the *reaching* (outer) guard, which is frequently NOT the slice of the guard that logically owns the rule.** When a consultant hands off a "guard A shadows guard B" finding, the REACH-determinant (what makes A reach first) can be a third slice (e.g. the Switcher = nlo-syntax). Cross-ref `dead-code-liveness.md` (reachability-before-mechanism) and `coupling-order-nlo-bracket-seams.md` (the `[...]` bracket parsed three times).

## Dispatch ordering

- "Why did my BSM/NLO process line raise" → nlo-syntax (guard firing order) first → coupling-order (if an order constraint) / amcatnlo (proc_validity, NLO) / eft+nlo-model (if loop-capability). Identify the OUTER reaching guard before describing the rule.
- "Check my amplitude is correct" (`check` command) → process-syntax (validator map) + madloop (the loop path runs MadLoop, extra loop tolerances/checks).
- "My NLO run flags unstable points / what's the return code" → madloop runtime-driver (RET_CODE, ##W03), NOT the `check` command.
