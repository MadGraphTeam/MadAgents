---
description: The ordered polarization-validation pipeline — five parse/construction-time gates, each with a distinct exception type/message; which gate a malformed {…} spec dies at, and why order is load-bearing
---

# Polarization validation pipeline — the ordered gates

A polarization `{…}` spec passes through **five validation gates** at parse /
construction time (all fire at `generate` / `add process`, before any `output`).
A malformed spec dies at the **first** gate it offends, with a gate-specific
exception type and message. Knowing the order lets you predict *where* a given
spec dies and *what error text* you'll see — including for specs none of the
instance pages individually name. Source-walked + probe-confirmed in v3.7.1.

## The gates, in firing order

| # | Gate | Where (v3.7.1) | Exception | Fires when |
|---|------|----------------|-----------|------------|
| 1 | **Placement / process-mode** | `madgraph_interface.py:check_process_format` 1191-1237 | `InvalidCmd` | `{}` in required s-channel, in forbidding (`$`/`/`) particles, in a plain-NLO process, or (NLO noborn/sqrvirt path) on a colored or massive leg |
| 2 | **Parse-entry** (name + multiparticle spin) | `extract_process` 5089-5109 | `InvalidCmd` | particle name not in model (`%s is not defined`); multiparticle members have ≠1 distinct spin (`...various spin`); non-whitespace `rest` after `}` (`A space is required...`) |
| 3 | **Letter / number mapping** | `extract_process` letter loop 5111-5190 | `InvalidCmd` | spin-gated letter on wrong spin (e.g. `"T" ... only ... spin one`); `abs>3` numeric (`polarization are between -3 and 3`); `0` on scalar/fermion; unknown char (`Invalid Polarization`) |
| 4 | **Value whitelist** (backstop) | `Leg.filter` 2143-2150 / `MultiLeg.filter` 2330-2337 | `PhysicsObjectError` | a value placed in the leg's `polarization` list is not in `list_of_allowed_polarizations` (2098) |
| 5 | **Ambiguous mix** | `Process.check_polarization` (base_objects 3869-3900) via `do_add` 3324-3332 | critical log + default-abort prompt → `InvalidCmd` | same final-state PID has a polarized leg and an unpolarized leg, or two polarized legs whose helicity values overlap |

## Why order is load-bearing
The gate that fires is the *first offended*, not the "most relevant":

- **Valid letter, wrong position → dies at gate 1, not 3.** `p p > Z{T} > e+ e-`
  → `InvalidCmd: Polarization restriction can not be used as required s-channel`
  (probe). `T` is a perfectly valid spin-1 letter; it is never read because
  placement rejects the s-channel `{}` first. So a placement error is NOT
  evidence the letters are wrong.
- **Gate 4 is currently an UNREACHABLE backstop.** The letter loop (gate 3) caps
  numeric helicities at `abs≤3` and only emits codes that are all already in the
  whitelist (`±1,0,±2,±3,4,5,6,7,9,99`). So no spec reaches gate 4 with an
  out-of-whitelist value — `Z{+4}` dies at gate 3 with `InvalidCmd: polarization
  are between -3 and 3`, NOT at gate 4 with `PhysicsObjectError` (probe). Gate 4
  is a pure consistency net: it would only fire if the letter loop and the
  whitelist drifted out of sync in a future version. The exception *type*
  (`PhysicsObjectError` vs `InvalidCmd`) is the tell that distinguishes gate 4.
- **Glued vs spaced is a gate-2-vs-gate-5 fork.** `Z{T}Z` (no space, one token)
  → the `rest` after `}` is the glued `Z` → gate 2 `InvalidCmd: A space is
  required after the "}" symbol to separate particles` (probe). `Z{T} Z` (spaced,
  two tokens) → both pass parse-entry, both legs build → gate 5 ambiguous-mix
  prompt. Visually near-identical specs, completely different gate and error. The
  fix the user needs differs: glued = add a space; spaced = the mix is genuinely
  ambiguous (polarize both, or neither). See `pol-letter-mapping.md` parse-entry.
- **Gate 5 is the only one that runs post-construction** — the leg objects are
  built and the Process assembled before `check_polarization` runs in `do_add`.
  So a spec that is individually well-formed on every leg can still die at gate 5
  for a cross-leg reason. It is also the only gate that *prompts* (default-abort)
  rather than hard-raising immediately.

## Probe matrix (v3.7.1, all confirmed)
- gate 1: `generate p p > Z{T} > e+ e-` → `...required s-channel`.
- gate 2: `define mix = Z e-; generate e+ e- > mix{T} ve~` → `...various spin`.
- gate 3 (bad letter): `generate e+ e- > Z{X} Z` → `Invalid Polarization`.
- gate 3 (abs>3): `generate e+ e- > Z{+4} Z` → `polarization are between -3 and 3`
  (proves gate 3 pre-empts gate 4).
- gate 5: `generate e+ e- > Z{T} Z` → critical + `Do you want to continue [no, yes]`
  default no → `Not supported syntax of type p p  > Z{T} Z`.

## How to use this
Given a failing polarization spec, read the exception **type and text** to locate
the gate, then consult the instance page for that gate:
- placement/process-mode → `pol-placement-restrictions.md`
- letter/number meaning → `pol-letter-mapping.md`
- whitelist / value codes → `pol-allowed-values.md`
- ambiguous-mix algorithm → `check-polarization.md`
- the live probe transcripts → `pol-parse-probes.md`

This page is the cross-cutting index; the instances carry the depth. Boundary:
all five gates are **parse/construction-time**. There is ONE further in-slice
consumption of the parsed polarization list **after** these gates, at
diagram-generation time (stage 3): the massless-boson `0`-strip and sole-`0`
process drop — see `pol-generation-expansion.md`. That is not a sixth validation
gate (it does not raise a polarization error; a sole-`0` massless drop surfaces as
`NoDiagramException`), but it is where the parsed list this slice produces is last
touched in-slice. Past that — the amplitude / helicity-sum computation that
consumes the surviving codes — is out of this slice (mc-integration / HELAS territory).
