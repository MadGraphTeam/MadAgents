---
description: SMEFTatNLO v1.0.3 operator settability by restriction (-LO vs -NLO) — two gates (restrict-card zeroed→internal fixed 0.0, coupling-ref count); cG/cpG/ctlS3/ctlT3/cblS3 settable at LO but zeroed/removed at NLO; cpG NOT available at NLO.
---

# SMEFTatNLO v1.0.3 — operator settability: -LO vs -NLO restriction

**Version pin: SMEFTatNLO v1.0.3** (`$MADGRAPH_INSTALL/models/SMEFTatNLO/__init__.py:__version__ = "1.0.3"`). Operator availability is version-dependent; this page is that version only.

Which Wilson coefficient you can actually *set and have take effect* depends on the restriction (`import model SMEFTatNLO-LO` vs `SMEFTatNLO-NLO`). Two independent gates:
1. **restrict-card value** — a coefficient given value `0` is demoted from external to internal (fixed 0.0) and its coupling/vertex pruned; nonzero placeholder keeps it a settable external.
2. **coupling references** — a coefficient with no reference in `couplings.py`/`CT_couplings.py` is *inert* (settable but no physical effect). See `smeftsim-anchored-taxonomy-and-gaps.md` for the inert/LO-only derivation.

## Source-grounded restrict-card lines
Both cards share line numbering (structurally parallel). LO nonzero → NLO zeroed for the five NLO-incompatible operators:

| coeff | lhacode | restrict_LO.dat | restrict_NLO.dat |
|---|---|---|---|
| cG   | 7  | `:105` 0.373465 (external) | `:105` 0.000000 (zeroed) |
| cpG  | 8  | `:106` 0.058888 (external) | `:106` 0.000000 (zeroed) |
| ctlS3| 19 | `:178` 0.960816 (external) | `:178` 0.000000 (zeroed) |
| ctlT3| 20 | `:179` 0.612688 (external) | `:179` 0.000000 (zeroed) |
| cblS3| 21 | `:180` 0.700332 (external) | `:180` 0.000000 (zeroed) |

Settable at BOTH orders (nonzero in both cards): ctp `:130`, ctZ `:131`, ctW `:132`, ctG `:133` (LO values 0.985616/0.160119/0.439563/0.334581; NLO 0.422728/0.049973/0.761901/0.866452 — placeholders, not physics).

## Runtime probe confirmation (`display parameters`)
Cheap probe, both imports exit 0. `display parameters` groups by type: `parameter type: ('external',)` = settable; `parameter type: ()` = internal/derived (not settable).

- **`SMEFTatNLO-NLO`**: `mdl_cpG = 0.0` appears under `parameter type: ()` (internal — NOT settable). `mdl_cG`, `mdl_ctlS3`, `mdl_ctlT3`, `mdl_cblS3` **absent entirely** (grep count 0 — fully removed). `mdl_ctG/ctp/ctZ/ctW` under `('external',)` (settable).
- **`SMEFTatNLO-LO`**: `mdl_cG = 0.373465` and `mdl_cpG = 0.058888` under `('external',)` (settable). `mdl_ctlS3/ctlT3/cblS3` present and settable. `mdl_ctG/ctp/ctZ/ctW` settable.

## Net operator-availability table (v1.0.3)
| operator | LO (-LO) | NLO (-NLO) | note |
|---|---|---|---|
| ctG, ctp, ctZ, ctW | settable | settable | wired at both orders |
| cpG (Higgs-gluon) | **usable** | **DISABLED** (pruned by restrict_NLO) | see caution below |
| cG | settable but **inert** (0 coupling refs) | removed | no physical effect at any order |
| ctlS3 | inert (declared, no couplings) | removed | |
| ctlT3, cblS3 | **LO-only** (wired at LO, removed at NLO — no counterterms) | removed | CT_couplings has 0 refs |

## Caution / correction — cpG at NLO
A common expectation that **cpG is available at NLO does NOT hold for this installed model version** (v1.0.3): `restrict_NLO.dat:106` zeroes it and the probe shows it demoted to an internal fixed `0.0`. Requesting a cpG contribution under `SMEFTatNLO-NLO` silently yields no cpG effect (parameter not settable). Flag this whenever a task wants the Higgs-gluon operator at NLO.

## Gap
Whether a **later SMEFTatNLO version re-enables cpG (or ctlT3/cblS3) at NLO** cannot be settled from this install — only v1.0.3 is present here. Re-verify against the restrict_NLO.dat + `display parameters` of the actual installed version before asserting NLO availability for any of the five LO-only/disabled operators.
