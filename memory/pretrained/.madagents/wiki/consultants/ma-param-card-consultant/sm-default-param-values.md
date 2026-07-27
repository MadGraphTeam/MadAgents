---
description: OPERATIVE default-sm param_card values come from the restrict_default.dat layer (probe-confirmed), NOT raw models/sm/parameters.py — the two DIFFER for MT/WT/ymb/ymt, and MC/Me/MM + all Wolfenstein are zeroed→dropped. Recipe to read each value at its coordinate; plus the MW/sw2-internal discriminator and the aEWM1+Gf+MZ EW input scheme.
---

# Default sm param_card: OPERATIVE (restrict_default) vs RAW parameters.py

`import model sm` auto-applies `restrict_default.dat`. Per the priority chain (UFO param → restriction → output → user → treatcards), the OPERATIVE default written into `<PROC_DIR>/Cards/param_card.dat` carries the **restrict_default.dat** values, NOT the raw `parameters.py` values — and for several parameters they DIFFER. Probe-confirmed by generating `p p > t t~` with default sm and reading the operative card (v3.7.1).

**This page caches the LOOKUP, not the numbers.** Read each value fresh at its coordinate — a stale cached number reads exactly as valid as the current one. The durable knowledge is: *which layer wins, which coordinate holds the operative value, and which params diverge / are dropped.*

**Prior version of this page reported the RAW `parameters.py` values as operative — WRONG.** That was the exact error `operative-default-is-restrict-value` warns against (reading only the raw UFO layer). The divergent params are flagged below; read both coordinates to see the divergence.

## MASS block — editable externals (operative)
Coordinate: `$MADGRAPH_INSTALL/models/sm/restrict_default.dat` MASS section (~L16-24). Recipe: read `MASS <id>` in the generated card, or the restrict card line.
- 5 (MB), 15 (MTA), 23 (MZ), 25 (MH): restrict value == raw parameters.py value (no divergence).
- **6 (MT): DIVERGES.** restrict_default sets it (~:19); RAW `parameters.py` (MT decl, ~:144) sets a different value. Operative = the restrict value. Read both to see the gap.
- **DROPPED (zeroed by restrict_default → inert "dependent" comment lines, not editable):** MC(4), Me(11), MM(13) — raw parameters.py declares nonzero masses for charm/e/μ, restrict zeroes them → they are MASSLESS in the operative default-sm card. (Confirm: no editable `4`/`11`/`13` line in the MASS block; only an inert `# c : 0.0`-style comment.)
- u/d/s (1,2,3): never declared external in parameters.py → intrinsically massless.
- **24 (MW): ABSENT from editable MASS.** MW is `nature='internal'`, `value='cmath.sqrt(MZ**2/2.+cmath.sqrt(MZ**4/4.-(aEW*pi*MZ**2)/(Gf*sqrt2)))'` (`parameters.py` MW decl ~:295-299). Appears in the card only as an inert dependent comment `24 <value> # w+ : cmath.sqrt(...)`. Cannot be overridden there; recomputed Fortran-side. (Load-bearing: the PDG MW value is NOT a free input of a default sm card — it is derived.)

## YUKAWA block (operative) — DIFFERS from both MASS and raw
Coordinate: `restrict_default.dat` YUKAWA section (~L47-53). Recipe: read `YUKAWA <id>` in the generated card.
- **5 (ymb): DIVERGES** from raw `parameters.py` (ymb decl ~:85). Operative = restrict value.
- **6 (ymt): DIVERGES** from raw `parameters.py` (ymt decl ~:93, the MSbar running mass). Operative = restrict value.
- 15 (ymtau): present, matches.
- **DROPPED:** ymc(4), yme(11), ymm(13) all zeroed → absent from editable YUKAWA (block holds only 5/6/15). A hand-added lepton-Yukawa line is inert (restriction-pruned-external-is-dropped).

## DECAY block (operative widths)
Coordinate: `restrict_default.dat` DECAY section (~L28-33). Recipe: read `DECAY <id>` in the generated card.
- **6 (WT): DIVERGES** from raw `parameters.py` (WT decl ~:205). Operative = restrict value.
- 23 (WZ), 25 (WH): present.
- 24 (WW): PRESENT (W WIDTH is external even though W MASS is internal; mass-vs-width nature independent).
- **DROPPED:** WTau(15) zeroed → inert dependent comment.

## SMINPUTS block (operative)
Coordinate: `restrict_default.dat` SMINPUTS + `parameters.py:37-43` (aS decl). Recipe: read `SMINPUTS <id>`.
- 1 (aEWM1): the **running** 1/α at M_Z (Gμ-region), NOT the Thomson-limit 1/α(0). Reading it as the Thomson value is the trap. Read the actual stored default at SMINPUTS 1.
- 2 (Gf): Fermi constant.
- 3 (aS): carries the `# aS (Note: this Parameter is not used if you use a PDF set)` comment → see sminputs-as-pdf-override (PDF/beam supersedes it run-side).

## Wolfenstein / CKM (operative)
`restrict_default.dat` Wolfenstein section (~L38-42) zeroes ALL four Wolfenstein inputs (lamWS/AWS/rhoWS/etaWS = 0; raw `parameters.py` (~:48/56/64/72) declares nonzero PDG-like values). → **NO editable Wolfenstein or CKM block in the operative card** (probe: 0 matches). CKM is derived internal (`parameters.py:229-281`) and with all Wolfenstein=0 evaluates to the **exact identity** (CKM1x1=1, off-diag=0), NOT "near-diagonal". So the default-sm operative card has EXACTLY-diagonal CKM, massless first/second-gen (except MB, MTA), diagonal-flavour physics. Mechanism (all-zero Wolfenstein → identity CKM, no editable block) is durable; the raw nonzero Wolfenstein values are drift-prone — read them at their decls if needed.

## EW input scheme — what is free vs derived
FREE (external) EW inputs: aEWM1 (SMINPUTS 1), Gf (SMINPUTS 2), MZ (MASS 23).
DERIVED (internal, never in editable card): aEW=1/aEWM1 (:283), MW (:295), ee=2√(aEW·π) (:301), sw2=1-MW²/MZ² (:307), cw/sw/g1/gw (:313+). So MW and weak mixing are OUTPUTS, not inputs. This is the α(M_Z)+Gf+MZ input set with MW derived — NOT the pure Gμ scheme (in pure Gμ, α is derived; here α is an input). A user quoting a fixed MW or sin²θw as a "set" default-sm value is wrong: they are computed.

## `set param_card` name/code resolution
`set param_card <block> <lhacode...> <value>` and bare param-NAME both work: do_set builds `pname2block` (name→[(block,lhaid)]), rewrites bare-name into block+id, calls `setP` (`common_run_interface.py` ~:6187-6197 → :6443). `set param_card mass 6 <val>` ≡ `set param_card mt <val>`.

## `set`-time Auto capitalization
`setP` (~:6450-6457) normalizes `auto`→`Auto`, `auto@nlo`→`Auto@NLO` (CAPITAL) and rejects auto for block≠'decay'. FILE-read path (check_param_card load) LOWERCASES to `auto`/`auto@nlo` (see width-representation-in-card). Token case differs by entry point; both round-trip.

## Caveat
"Default sm" values are software conventions on the restrict_default layer, NOT PDG pole values, and NOT the raw parameters.py numbers. Always quote the OPERATIVE (restrict-card / generated-card) value read fresh at its coordinate. A value quoted without "operative default sm" has no provenance.
