---
description: Precondition-gated cut auto-disable — a kinematic cut whose enabling precondition is unmet (a superseding feature is active, or its target particle class is absent) is silently ZEROED, never enforced; the user-facing tell is a "discarded"/"will be ignored" warning, not a value-swap. Distinct from the layer-precedence law.
---

# Precondition-gated cut auto-disable

Source: `$MADGRAPH_INSTALL/madgraph/various/banner.py` (RunCardLO.check_validity) and
`$MADGRAPH_INSTALL/Template/LO/SubProcesses/setcuts.f` (ERROR TRAPS). MG5_aMC v3.7.1.

## The principle
A kinematic cut is enforced ONLY if its enabling precondition holds. When the precondition
is unmet, MadGraph does not error and does not enforce a clamped value — it **silently zeroes
the cut** and emits an advisory warning. The precondition that fails is one of two kinds:

- **(A) A superseding feature is active**, so the cut is redundant/inconsistent with it.
  Frixione photon isolation supersedes the fixed photon cuts; MLM matching supersedes the
  jet-jet separation cuts.
- **(B) The cut's target particle class is absent** from the final state, so the cut has
  nothing to act on (the "at-least-one-of-class" `xptX` cuts and the VBF rapidity-gap cut).

The operational tell is therefore a **warning line in the log**, not a value-swap. This is
WHY a user can set a cut, see no error, and find it had no effect: it was dropped, not
clamped to a different number. (Contrast the layer-precedence law in
cut-value-layer-precedence.md, which is about the SAME datum being overwritten to a DIFFERENT
value, latest layer winning — there the value changes; here it goes to zero/off.)

## The sites (instances)
Kind A — superseding feature (parse-time, banner.py check_validity):
- :4516-4522 `ptgmin>0` (isolation active) => `pta=0.0` (warn "pta cut discarded since photon
  isolation is used"), `draj=0.0` (warn "draj cut discarded..."). The photon still gets a pt
  FLOOR via setcuts.f:300 `etmin=max(pta,ptgmin)`; only the user pta/draj are dropped.
- :4566-4577 `xqcut>0` (matching) => `drjj=0`, `drjl=0` (warn "Since ickkw>0, changing ...to 0"),
  and `mmjj=0` if `not auto_ptj_mjj and mmjj>xqcut` (warn "MMJJ set to 0").

Kind B — target class absent (runtime, setcuts.f ERROR TRAPS, :835-880):
- :835-838 no jets & `xptj>0` => `xptj=0`, warn "cuts on the jet will be ignored".
- :840-843 <2 jets & `xetamin>0 .and. deltaeta>0` => `xetamin=deltaeta=0`, warn "WBF cuts not
  will be ignored" (VBF rapidity-gap needs >=2 jets).
- :846-880 same shape for `xpta` (no photons / "cuts on the photon will be ignored"),
  `xptb` (no b / "...b-quarks..."), `xptl` (no leptons / "...lepton...").

## Why this catches MORE than the instances
The instances enumerate today's sites. The principle predicts the SHAPE for any cut not in
this list: if a cut's precondition (superseding feature active, or target class absent) fails,
expect silent-zero + advisory warning, NOT a hard error and NOT a clamped value. So the
debugging move for "I set cut X and it did nothing" is: (1) check whether a superseding
feature (isolation `ptgmin>0`, matching `xqcut>0`) is on; (2) check whether X's target class
is present in the final state; (3) grep the run/survey log for a `discarded` / `will be
ignored` warning. The card may still SHOW the value: parse-time (Kind A) edits are written
back to run_card.dat, but runtime ERROR-TRAP (Kind B) zeroing happens in setcuts.f memory and
is recorded ONLY in the survey log — never in any card.

## Boundary
- This is auto-DISABLE (value -> 0/off). The auto-OVERRIDE-to-a-different-value cases
  (`ptj=mmjj=xqcut` forced under matching, PDG cuts overwriting etmin by PDG) belong to the
  layer-precedence law (cut-value-layer-precedence.md), not here — different prediction.
- Kind-A warnings only fire `if X in self.user_set` for drjj/drjl (silent if the value was
  auto-set, not user-set); the zeroing happens regardless of user_set. pta/draj/mmjj warn
  unconditionally when the branch fires.
- The ERROR TRAPS are advisory: the two `etmin==0 .and. emin==0` jet/gamma warnings
  (setcuts.f:819-825) only warn, they do NOT change values — those are advice, not a disable.
- LO path only. NLO (amcatnlo setcuts) out of slice.

## Probe-confirmed (v3.7.1)
`generate p p > t t~; output; set xpta=30 (no photons in final state); generate_events`:
- Survey log prints VERBATIM `Warning: cuts on the photon will be ignored` (setcuts.f:854) —
  Kind-B absent-class auto-disable fired at runtime, xpta dropped to 0.
- Same run, `Define smin to 119716.0` printed (setcuts.f:708) and printed cut table shows
  `Et > 50.0 50.0` on the two tops from `pt_min_pdg {6:50}` — confirms the PDG-cut/smin
  mechanism alongside (pdg-cuts-and-smin.md), and that the trap is independent of it.

## Instances (kept)
- runcard-cut-validity.md — Kind A (photon-iso + matching parse-time disables).
- pdg-cuts-and-smin.md §5 — Kind B (setcuts.f ERROR TRAPS).
- cuts-f-filter.md "Mapping layer" — the etmin=max(pta,ptgmin) floor that survives Kind-A pta zeroing.
