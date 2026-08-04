---
description: Emitted matrix.f entry points (SMATRIX/MATRIX) and the |M|^2 averaging structure — IDEN composition (spin*color*identical) via get_denominator_factor, DENOM color common-denominator, helicity-sum loop, IC flow array. Verified against a generated standalone gg>ttx + uu~>ttx.
---

# matrix.f entry points and |M|^2 averaging (SMATRIX / MATRIX / IDEN / DENOM)

Verified against a live `output standalone` for `g g > t t~` and `u u~ > t t~` (v3.7.1), plus
`$MADGRAPH_INSTALL/madgraph/iolibs/export_v4.py` (writers) and
`$MADGRAPH_INSTALL/madgraph/core/helas_objects.py` (get_denominator_factor). Generated file cited as `matrix.f@N`.

## Two entry points and where each division happens
- `SUBROUTINE SMATRIX(P,ANS)` (matrix.f@33). Loops `DO IHEL=1,NCOMB` (matrix.f@157), `T=MATRIX(P,NHEL(1,IHEL),JC(1))` (@164), `ANS=ANS+T` (@167), then **`ANS=ANS/DBLE(IDEN)`** (@175). So IDEN division happens ONCE in SMATRIX, after the helicity sum. Returns |M|^2 summed over all helicities+colors, averaged.
- `REAL*8 FUNCTION MATRIX(P,NHEL,IC)` (matrix.f@189). Single helicity config NHEL + flow array IC. Color-summed via CF then **`MATRIX = MATRIX / DENOM`** (@278). NO IDEN division here (docstring @195 "no average over initial state/symmetry factor"). DENOM applied inside MATRIX, IDEN inside SMATRIX.

## The color sum in MATRIX is a PACKED upper-triangular form, not a full CF(j,i) matrix
matrix.f@226 `INTEGER CF(NCOLOR*(NCOLOR+1)/2)` — CF is a 1-D packed array of the upper triangle, NOT CF(NCOLOR,NCOLOR). Loop @270-277:
```
DO I=1,NCOLOR; ZTEMP=0; DO J=I,NCOLOR; CF_INDEX++; ZTEMP+=CF(CF_INDEX)*JAMP(J); ENDDO
  MATRIX += REAL(ZTEMP*DCONJG(JAMP(I))); ENDDO
```
Only J>=I traversed; off-diagonal CF entries are **pre-doubled** so the single triangle recovers the full symmetric double sum. Writer: `get_color_data_lines` (export_v4.py@1250). Symmetric case stores upper diagonal only (`min_k=index` @1271) and multiplies off-diagonal numerators by 2 (`(1 if (k==index and pos==0) else 2)*int(i)` @1281); asymmetric (col_basis1 != col_basis2, e.g. loop/interference) uses full `CF(i,index)` 2-D (@1275). For gg>ttx: `DATA (CF(I),I=1,2)/16,-4/` and `/16/` (matrix.f@242-244) — diag 16, off-diag -4 = 2*(-2). The standard color-sum `sum_{i,j} CF(j,i)*JAMP(j)*conj(JAMP(i))` is the MATH the packed loop computes, but the emitted array is triangular+doubled, not a full matrix. (CF/DENOM VALUES are color-decomposition's derivation; the PACKING/consumption is this slice.)

## IDEN = spin_factor * color_factor * identical_particle_factor (ALL folded into IDEN)
`HelasMatrixElement.get_denominator_factor()` (helas_objects.py@4910, formula resolves v3.7.1), emitted by `get_den_factor_line` (export_v4.py@1289 `"DATA IDEN/%2r/"`). Body @4919-4931 — three factors, each DERIVED per process from its initial legs:
- `color_factor` = product over INITIAL legs of `particle.get('color')` (@4919), i.e. the color-rep dimension per initial leg. Gluon → 8; quark/antiquark → 3 (the antiquark's stored `'color'` enters as +3, NOT -3 — a colored qq̄ initial state gives factor 9, generated-verified as +36 not -36); colorless initial (e.g. e+/e-) → 1.
- `spin_factor` = product over INITIAL legs of `len(get_helicity_states())` (or `len(polarization)` if partially polarized) (@4924) — # helicity states per initial leg (massless vector / fermion → 2).
- `identical_particle_factor` = n! for n identical final-state legs (e.g. two identical FS gluons → 2). The **final-state 1/n! is FOLDED INTO IDEN** as an integer multiplier, NOT handled separately. (idpart itself = `Process.identical_particle_factor()`, base_objects.py — see idpartfactor-not-idmetag lesson.)
- `return spin_factor * color_factor * self['identical_particle_factor']` (@4931).

DERIVE IDEN per process from these three factors and read the emitted value fresh at `matrix.f` `DATA IDEN/.../`; do NOT cache a process→IDEN table. **Example for this one topology (derive per process for anything else):** `g g > t t~` → 8·8 (color) · 2·2 (spin) · 1 (idpart) = 256, matching generated `DATA IDEN/256/`.

## DENOM is a color common-denominator, process-dependent, NOT initial-color averaging
DENOM is the common denominator that renders the rational CF matrix as integers — writer `get_color_data_lines` @1259-1260: `Denom = max(color_matrix.get_line_denominators())`; colorless ME → `DATA Denom/1/, DATA CF/1/` fallback (@1255). It is NOT initial-color averaging: that average lives in IDEN, not DENOM, so a process can carry DENOM=1 while its initial-color-average factor sits inside IDEN. DERIVE per process and read the emitted `DATA DENOM/.../` fresh. **Example (this topology only):** gg>ttx emits `DATA DENOM/3/` (matrix.f@241) while its initial-color-average factor 9 lives in IDEN — confirming DENOM ≠ color averaging. (Derivation of the color_matrix rationals is color-decomposition's; consumption in matrix.f is this slice.)

## IC flow array and NHEL feed
SMATRIX sets `JC(IHEL)=+1` (matrix.f@137) and passes `JC(1)` as IC. In MATRIX each external's HELAS call takes `<sign>*IC(i)` as the NSV/flow arg: `VXXXXX(P(0,1),ZERO,NHEL(1),-1*IC(1),W(1,1))` (@250, incoming gluon sign -1), `OXXXXX(...,+1*IC(3),...)` outgoing t (@252), `IXXXXX(...,-1*IC(4),...)` incoming t~ (@253). The fixed +/-1 encodes the particle's own in/out state; IC(i) toggles it for crossing (IC=+1 standard, IC=-1 reversed). NHEL(i,IHEL) supplies the helicity per external. (The VXXXXX/IXXXXX/OXXXXX internals are aloha's; only the NHEL/IC feed is this slice.)

## Subtleties / cautions
- SMATRIX does NOT unconditionally sum all NCOMB helicities: helicity filtering (`GOODHEL`, warmup `NTRY<20` @159), single-helicity `USERHEL` selection (@158), and polarization `IS_BORN_HEL_SELECTED` gating (@160-166) can skip configs. `HELRESET` clears GOODHEL (@124). `NEXTERNAL<=3` disables filtering (spin-2 boost caveat, @151-155). The plain unpolarized inclusive path is the `ANS/IDEN` @175 line.
- `HELAVGFACTOR` (=4 here) and `BEAMS_HELAVGFACTOR` (/2,2/) are used ONLY in the USERHEL / polarized branches (@176-185) to RE-multiply and undo the initial-spin averaging when a specific helicity or beam polarization is requested — they do NOT enter the standard unpolarized result.
- This is the standalone exporter's matrix.f. The madevent `matrix1.f` has the same SMATRIX/MATRIX/IDEN/DENOM skeleton but additional multichannel (AMP2/ICONFIG) and JAMP-recycling machinery; entry-point + averaging structure is shared.
