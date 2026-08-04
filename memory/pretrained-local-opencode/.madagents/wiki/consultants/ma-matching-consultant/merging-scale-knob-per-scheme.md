---
description: Cross-scheme principle — "the merging scale" is not one parameter. Each matching scheme reads its merging scale from a scheme-specific run-card/shower-card knob (xqcut / ktdurham|ptlund / ptj / Qcut) and, for LO+PS, writes a scheme-specific Pythia8 target with a scheme-specific ratio (1.5× / 1:1 / raw). Routes "where/what is the merging scale for scheme X" without reading four instance pages.
---

# Merging scale: scheme-specific knob, file, and Pythia8 ratio

There is NO single "merging scale" parameter in MadGraph. Asking "what is the
merging scale" without naming the scheme is ill-posed — each scheme reads its
scale from a DIFFERENT knob, in a DIFFERENT card file, and (for the LO+PS
schemes that hand off to Pythia8) writes a DIFFERENT Pythia8 target with a
DIFFERENT ratio. This page is the navigation map; the per-scheme mechanics are
on the instance pages.

## The map (all static-source)

| Scheme | Generation knob (file) | Pythia8 target | Ratio | Source |
|---|---|---|---|---|
| MLM (LO ickkw=1) | `xqcut` (run_card) | `JetMatching:qCut` | **1.5× xqcut** | `madevent_interface.py:4409` |
| CKKW-L (LO+PS) | `ktdurham` *or* `ptlund` (run_card) | `Merging:TMS` | **1:1** (= cut) | `madevent_interface.py:4514` |
| FxFx (NLO ickkw=3) — generation | `ptj` (run_card) | — (Fortran cut) | cut vs lowest FKS clustering scale | `Template/NLO/SubProcesses/cuts.f:480` |
| FxFx (NLO ickkw=3) — shower | `Qcut` (**shower_card**) | `qcut` | 1:1 | `shower_card.py:180` (`py8='qcut'`) |
| UNLOPS (NLO ickkw=4) | `ptj` (run_card) | — (Fortran `pythia_UNLOPS`) | first-cluster + Born cut | `cuts.f` (`passcuts_unlops_jv`) |
| jet-veto (NLO ickkw=-1) | `ptj` (run_card) | — | `pt(QCD) > ptj` veto | `cuts.f` (`passcuts_unlops_jv`) |

Key consequences a single-page reader misses:
- **The knob's CARD FILE changes between LO and NLO.** LO MLM/CKKW scales are
  run_card params; the FxFx *shower* scale is a **shower_card** param (`Qcut`).
  There is **no `xqcut` in the NLO run_card at all** (nlo-ickkw-fxfx confirms no
  registration in `RunCardNLO`). A user porting `xqcut` to an NLO card is setting
  a non-existent parameter.
- **The PY8 ratio differs.** MLM writes `JetMatching:qCut = 1.5*xqcut` (NOT equal
  to xqcut); CKKW writes `Merging:TMS = cut` 1:1. So "PY8 qCut == my generation
  cut" is true for CKKW, false for MLM.
- **FxFx has TWO scales, not one.** `ptj` (run_card) is the *generation* cut
  (against the lowest FKS clustering scale); `Qcut` (shower_card) is the
  *Pythia8-side* matching scale. A consistent FxFx run requires setting BOTH.
- **The systematics-variation floor tracks the ratio.** The `sys_matchscale`
  factor sweep drops factors below `1.5*xqcut` for MLM but below the raw
  `run_card[CKKW_cut]` for CKKW — because the central PY8 scale is 1.5× for MLM
  and 1:1 for CKKW (sys-matchscale-variation).

## The navigational rule

Given a "where/what is the merging scale" question:
1. Classify the scheme (ickkw value / LO-vs-NLO / which downstream tool).
2. Name the **knob + card file** from the table — never assume `xqcut`.
3. If LO+PS, name the **PY8 target + ratio** — never assume 1:1.
4. If FxFx, name **both** scales (run_card `ptj` AND shower_card `Qcut`).

## Why this catches MORE than the instance pages

Each instance page (mlm-py8-bridge, ckkwl-durham-lund, fxfx-unlops-fortran-cut,
shower-card-qcut) describes ONE scheme's scale in isolation. None states the
cross-scheme invariant that the knob, the file, and the ratio ALL vary by
scheme. The recurring real-world errors this prevents — "set xqcut at NLO",
"PY8 qCut should equal my cut", "FxFx merging scale is in the run_card", "one
merging scale covers the whole run" — are each a failure to consult the OTHER
scheme's page. The map answers them in one lookup.

## Boundary
- This is the **static knob→target→ratio mapping only**. The runtime merging
  scale *values*, the fraction of events cut, and the actual PY8 veto behavior
  are launch-time — probe-candidates, owned by the instance pages' caution
  blocks, not asserted here.
- The Pythia8-side *execution* of the matching (how PY8 applies qCut/TMS) is the
  pythia8-interface slice. This page maps only what MadGraph writes.
- `pdgs_for_merging_cut` (which PDGs the cut applies to — default list gluon +
  light quarks, read fresh at `banner.py:4423`, overwritten with `colored_pdgs`
  at auto-detect) and
  `maxjetflavor`/`asrwgtflavor` (flavour ceilings) are separate knobs — they
  scope WHICH partons the cut sees, not the scale value. See lo-ickkw-mlm.
