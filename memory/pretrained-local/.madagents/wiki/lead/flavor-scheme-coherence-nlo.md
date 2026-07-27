---
description: A b-quark in the initial or final state, or a b-PDF, with an NLO QCD calculation. 4F versus 5F is in play.
---

# Flavor-scheme (4FS/5FS) coherence at NLO — the un-enforced invariant

A b-quark NLO process is consistent only if **one** flavor scheme is chosen coherently across four independently-owned pieces:

| piece | 4FS (massive b) | 5FS (massless b) | owner |
|---|---|---|---|
| model import (b mass) | `import model sm` (M_b≠0) | `sm` + `restrict_no_b_mass` (M_b=0, y_b=0) | model-loader / restriction |
| b in default `p`/`j` | **absent** (mass-driven) | **present** | model-loader |
| `maxjetflavor` | 4 | 5 | scales-pdf (auto from beam content) |
| PDF n_f | 4-flavor set | 5-flavor set (b-PDF active) | scales-pdf / external LHAID |

**MG enforces none of the cross-checks.** There is no code path that reads the PDF's n_f and compares it to `maxjetflavor` or to the b mass; a mismatched spec parses clean and launches. At LO the mismatch is "merely" a wrong cross-section; **at NLO it becomes a hard failure** — the IR poles of the virtual and the integrated counterterm no longer cancel.

## Why the mismatch is fatal at NLO (the FKS-visible half)

FKS soft/collinear singularity classification is **massless-keyed** — mass is the sole predicate (`fks_common.py:516-567`); there is no is-initial-state branch and no mass tolerance. Consequence for a **massive** b against a **5-flavor** PDF:

- `b → b g` ISR **is** subtracted (the gluon is massless → soft).
- `g → b b̄` collinear ISR is **not enumerated** — the `nsoft` gate (`fks_common.py:282`) requires a massless splitting product, and neither leg of `g→bb̄` is massless when the b is massive.
- But the 5F PDF was **DGLAP-evolved** with a massless `g→bb̄` splitting kernel and carries the matching collinear PDF counterterm.

So the counterterm the PDF expects has no real-emission subtraction term to cancel against → the integrated poles miss → `check_poles` fails at runtime (`amcatnlo_run_interface.py:5746`, deviation reported when >10%; message "Poles do not cancel"). The reverse mismatch (massless b, 4F PDF with no b-PDF) breaks the same bookkeeping from the other side.

That enumeration asymmetry is the **source-visible** half. The full pole-matching argument (why the DGLAP counterterm and the massive-b virtual log(m_b) cannot line up) is first-principles + nlo-export territory — route it to `ma-physics-consultant` / nlo-export, do not assert it from the FKS enumeration alone.

## The IR-pole check is a detector, not a fix

`IRPoleCheckThreshold` (`FKSParams.dat` / `FKSParams.f90`, default registered there — read it at the `FKSParams.f90` coordinate; enforced at `check_poles.f` and `BinothLHA.f`) can be set to `-1.0d0` to **disable** the check. Disabling does not fix a scheme mismatch — it **masks** a genuine inconsistency, and the run then produces a silently-wrong σ. Never recommend disabling the pole check as a remedy for a b-scheme failure; the remedy is a coherent scheme.

## Owner map (route each ingredient to its slice)

- **model-loader** — b-in-`p`/`j` is mass-driven (`b['mass']=='ZERO'` test, `madgraph_interface.py:6050-6058`); `import model sm` vs `sm-no_b_mass` decides the whole cascade.
- **restriction** — `restrict_no_b_mass.dat` zeros both M_b **and** y_b (Yukawa); the massless-b scheme drops any y_b-mediated contribution, not just the kinematic b mass.
- **scales-pdf** — `maxjetflavor` default / auto-set-from-beam-content; the **no-guard** fact (PDF n_f never read); external-LHAID n_f identity.
- **kinematic-cuts** — `maxjetflavor` splits the jet vs b-jet cut application (`setcuts.f:217-221`, `banner.py:4424`); a b counted as a light jet vs a b-jet changes which cut fires.
- **fks** — the massless-keyed soft/collinear classification and the massive-b `g→bb̄` drop above.

## Dispatch discipline

The scheme is a **whole-spec invariant owned by no single slice**, so no consultant will flag the mismatch on its own — each answers its own ingredient correctly. The **lead** reconciles the four rows by hand before launch (a whole-spec reconciliation step). When a b-process NLO run is on the table, state the scheme explicitly, verify all four rows agree, and treat a clean parse as no evidence at all that they do — this seam exists precisely because the clean parse hides the mismatch until the pole check fires (or, if disabled, never).

## Siblings
- `matching-merging-fanout.md` — carries the LO-matched-sample form of the same flavor-scheme seam (its "Cross-slice seam — the flavor-scheme invariant" section); this page is the NLO / IR-pole-cancellation form. The un-enforced-n_f fact is shared.
- `pdf-and-scale-configuration-fanout.md` — the general PDF/scale fan; `maxjetflavor` and the 4F/5F↔PDF coherence live there for the non-b case.
- `removed-coupling-not-small.md` — the y_b=0 side of `restrict_no_b_mass` is an instance (a Yukawa contribution removed, not made small).
