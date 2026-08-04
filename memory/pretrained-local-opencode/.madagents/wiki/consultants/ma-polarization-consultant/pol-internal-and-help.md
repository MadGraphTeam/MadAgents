---
description: Polarization on internal/decaying particles (decay-chain head allowed, required-s-channel rejected) and the help_polarization runtime prerequisites (group_subprocesses/nhel/me_frame)
---

# Polarization on internal particles + the help_polarization prerequisites

Two related facts, source-walked v3.7.1. Both clarify the user-facing surface of
the slice (where `{}` is allowed beyond simple final states, and what the run
needs downstream).

`help_polarization` is at madgraph_interface.py:**762-773** (v3.7.1); the British
spelling `help_polarisation` (774-776) just points the user to `help polarization`.

## 0. The three official help examples (documented allowed forms)
The help text (766-768) ships three canonical examples — these are the
documentation's own statement of what is allowed, and two of them are the concrete
disjoint-polarization-same-PID cases that `check-polarization.md` describes
abstractly:
- `generate t{L} > w+{T} b{R}, w+ > ta+ vt` — polarization on a **decay-chain head**
  (`t{L}`) and on chain final/heads (`w+{T}`, `b{R}`); see §1 below.
- `generate p p > z{T} z{A}, z > e+ e-` — **two polarized Z's, same PID 23, DISJOINT
  codes** (`{T}`=[1,-1] vs `{A}`=[99]). Helicity values don't overlap → passes the
  ambiguous-mix gate (`check-polarization.md`). This is the documented sanctioned use
  of two differently-polarized copies of one PID.
- `generate p p > z{0} z{T}, z > e+ e-, z > mu+ mu-` — `{0}` (longitudinal, Z is
  massive so `0` is NOT stripped — contrast the massless-boson 0-strip in
  `pol-generation-expansion.md`) + `{T}`, again disjoint codes on PID 23, with two
  separate decay chains.

So the official examples themselves demonstrate: polarization on decay-chain heads,
and disjoint-helicity multiple-polarized-copies of one PID (allowed), in contrast to
the polarized+unpolarized mix (rejected, §check-polarization).

## 1. "Internal/massive particle" polarization = decay-chain head, NOT s-channel
`help_polarization` (madgraph_interface.py:762-773) advertises:
> "Fix the helicity polarizations of external particles (massless or massive) or
> **massive internal particles** before decay chain by adding '{X}' to (multi)particles"
> Example: `generate t{L} > w+{T} b{R}, w+ > ta+ vt`

This appears to contradict the placement gate `pol-placement-restrictions.md` §1
("can not be used as required s-channel"). The resolution is **which kind of
internal placement**:

- **Decay-chain head — ALLOWED.** In `t{L} > w+{T} b{R}, w+ > ...` the `t{L}` is
  the decaying head of a chain segment and `w+{T}` is both a final-state of the
  top segment and the head of its own decay. Each `>`-separated comma segment is
  parsed as its own subprocess; the polarized particle is a leg of that
  subprocess, so it passes `extract_process`. **Probe-confirmed (v3.7.1):**
  `generate t{L} > w+{T} b{R}, w+ > ta+ vt` → "1 processes with 2 diagrams",
  no error.
- **Required s-channel middle — REJECTED.** The placement gate only inspects
  `particles_parts[1]`, i.e. the *middle* segment of a two-`>` process
  `a > X > b` (check_process_format 1191-1193). A `{` there raises
  `InvalidCmd('Polarization restriction can not be used as required s-channel')`.
  Probe: `generate p p > Z{T} > e+ e-` → that error (see pol-parse-probes via
  pol-validation-pipeline gate 1).

So "internal particle polarization" is real but reached through **decay-chain
syntax**, never through the `> X >` required-s-channel slot. The comment at 1189
("'{}' should only be used for onshell particle (including initial/final state)")
is consistent: a decay-chain head is on-shell for its segment; a required
s-channel particle is the off-shell propagator being forced, hence rejected.
(Decay-chain syntax itself — comma segments, what a "head" is — is the
process-syntax slice's territory; this page only covers where `{}` may sit.)

## 2. help_polarization names three RUNTIME prerequisites (slice boundary pointer)
`help_polarization` (762-772) also states (line 769-770):
> "Users need to set **'group_subprocesses False'**, **'nhel=1' (run_card)**, and
> **'me_frame' (run_card)**"
> "For the process 'p p > w+ z j j, w+ > l+ vl, z > l+ l-', the WZ rest frame is
> given by `me_frame = [3,4,5,6]`"

These three are **out-of-slice settings** (group_subprocesses → process-grouping;
nhel → numerical/helicity-sum slice; me_frame → numerical / run_card slice). What
IS in slice: the *fact that the polarization help directs the user to set them*,
and the semantics that `me_frame` lists the 1-indexed legs whose combined rest
frame defines the helicity-quantization axis (here legs 3,4,5,6 = the W and Z
decay products → the WZ rest frame). Cited references: appendices of
[arXiv:1912.01725] and [arXiv:2512.10015]; loop-induced in [2401.17365]
(771-772).

### Why this matters for a polarized job
A polarized process that *parses* fine can still give wrong/meaningless results at
integration if these run_card settings are not applied — the helicity basis is
frame-dependent and grouping/recycling can mix helicity states. The parse-time
gates this slice owns do NOT enforce these run_card settings; they are the user's
responsibility per the help text. **Route the run_card mechanics (nhel,
me_frame, group_subprocesses) to the numerical / run_card slices.** This page is
only the pointer: "polarization help says you need them."

## Caution
- **"Polarization is external-only / cannot restrict intermediate particles" (doc
  claim) is an oversimplification.** Two corrections: (a) a decay-chain HEAD *can* be
  polarized (`t{L} > w+ b` parses, §1) — it is internal to the full process but
  external to its chain segment; the flat "external only" wording is wrong for chains.
  (b) The genuinely-rejected case is the **required s-channel** slot `> Z{T} >`
  (placement gate, §1 / `pol-placement-restrictions.md`), rejected at PARSE — not
  because "the ME sums over intermediate polarizations". That summation is the
  amplitude/HELAS-computation rationale (helas-amplitude slice), not a fact this
  parser-side slice establishes. My slice confirms only: s-channel `{}` dies at the
  placement gate; chain heads pass.
- The "1 process / 2 diagrams" probe count is v3.7.1-specific; the load-bearing
  fact is that the decay-chain spec *parses without a polarization error*, not
  the exact count.
- `me_frame` indexing (1-based, which legs) is read off the help example only;
  the run_card parsing of `me_frame` is not in this slice — do not assert its
  parse behavior from this page.
