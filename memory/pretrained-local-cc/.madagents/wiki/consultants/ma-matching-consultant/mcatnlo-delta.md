---
description: MC@NLO-Delta matching mode (NLO) — run-card mcatnlo_delta flag, Pythia8-only validity gate, and the DELTA=ON shower-control write-out (MadGraph side).
---

# MC@NLO-Delta matching (run_card `mcatnlo_delta`)

A distinct NLO+PS matching variant from plain MC@NLO, ref arXiv:2002.12716. This page covers the MadGraph-side config knob and its gates only; the FKS/MC-subtraction internals are the NLO-FKS slice's.

## Registration (RunCardNLO)
- `$MADGRAPH_INSTALL/madgraph/various/banner.py:5670`: `self.add_param('mcatnlo_delta', False)`. Boolean, default `False`. Not gated by `ickkw` — it is an orthogonal NLO matching-mode flag, independent of FxFx (ickkw=3).
- Template comment `$MADGRAPH_INSTALL/Template/NLO/Cards/run_card.dat:97`: `%(mcatnlo_delta)s = MCatNLO_DELTA ! use MC@NLO-Delta matching, arXiv:2002.12716` with continuation "(only with Pythia8309 or later)". It sits in the parton_shower block (next to `parton_shower`, `shower_scale_factor`), not the merging block.

## Validity gate (Pythia8-only)
- `$MADGRAPH_INSTALL/madgraph/various/banner.py:5934`: `if self['mcatnlo_delta'] and not self['parton_shower'].lower() == 'pythia8':` → `raise InvalidRunCard("MC@NLO-DELTA only possible with matching to Pythia8")`.
- This is an ABORT-tier check (raises; run stops) per the matching-abort-vs-warn rule — malformed combo (Delta with a non-PYTHIA8 shower is unsupported). Not warn-only.

## Shower-control write-out (interface side)
- `$MADGRAPH_INSTALL/madgraph/interface/amcatnlo_run_interface.py:4783-4786`: writes `DELTA=ON` (else `DELTA=OFF`) into the shower run-control content, alongside `ICKKW=%s` and `PTJCUT=%s`. So the run-card flag is propagated to the aMC@NLO shower driver as the `DELTA` switch.
- `$MADGRAPH_INSTALL/madgraph/interface/amcatnlo_run_interface.py:5242`: `if mode in ['NLO','LO'] or not self.run_card['mcatnlo_delta']:` → writes DUMMY `pythia8_opts` / `pythia8_control_setup.inc`. Real Pythia8 link/setup files are written ONLY when `mcatnlo_delta` is on AND mode is not fixed-order (NLO/LO). I.e. Delta requires the Pythia8 C++ link path; plain (non-Delta) showered runs use the dummy.

## Fortran consumers (boundary — NLO-FKS slice)
`mcatnlo_delta` flows into the Fortran via `common /cMCatNLO_Delta/` (`$MADGRAPH_INSTALL/Template/NLO/Source/run.inc:70-71`) and is consumed in `montecarlocounter.f` (@544,550,681…), `fks_singular.f`, `handling_lhe_events.f`, `check_events.f`. What it changes in the MC-subtraction counterterms / FKS partner selection is the NLO-FKS slice's territory — not asserted here.

## Cautions
- Distinct from FxFx. A user can set `mcatnlo_delta=True` with `ickkw=0` (no merging) — it is a matching *mode* on a single-multiplicity NLO+PS run, not a multi-jet merging scheme. The two are not mutually exclusive at the parameter level.
- Hard Pythia8 requirement: non-PYTHIA8 `parton_shower` aborts (banner.py:5934). HERWIG/PYTHIA6 cannot do Delta.
- "(only with Pythia8309 or later)" version note is in the template comment, not enforced by any Python gate — `grep 8309|8.309|309` is clean across `banner.py`, `shower_card.py`, `amcatnlo_run_interface.py`. The only Python gate is the PYTHIA8-vs-other check @5934; the 8.309 minimum is documentation-only, so a too-old Pythia8 would fail downstream (at the shower/link stage), not at card-parse. (Source-read + grep-confirmed; not probe-verified.)
- The DELTA=ON write-out and the dummy-vs-real pythia8_opts switch are static-source facts; the actual aMC@NLO shower-driver execution is downstream (amcatnlo / pythia8-interface slices).
