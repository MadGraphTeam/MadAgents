---
description: decayBW.inc runtime artefact — per-subprocess line format data gForceBW(leg,iconfig)/value/, configs.inc s/t-channel dependency, parse-time probe, and the comma-vs-arrow gForceBW=1/0 contrast (chain-decay origin of the cut_decays/from_decay seam).
---

# decayBW.inc runtime artefact

Written by `write_decayBW_file` (export_v4.py:5879) into `<PROC_DIR>/SubProcesses/<P_n>/decayBW.inc` at output time.

## Line format
Source line (export_v4.py:5892-5894):
```python
lines.append("data gForceBW(%d,%d)/%s/" % (leg.get('number'), iconf + 1, booldict[leg.get('onshell')]))
```
- `%d` #1 = `leg.get('number')` — the leg number of the s-channel vertex's resulting (mother) leg. These come out low/negative because `get_s_and_t_channels` renumbers the resulting leg to `min()` of its contributors (helas_objects.py:1983/2039 — see onshell-helas-bridge.md), not by a "internal ⇒ negative" rule. (The FortranWriter upcases to `DATA GFORCEBW(...)`.)
- `%d` #2 = `iconf + 1` — 1-based diagram/config index. Same leg can recur across multiple iconfigs.
- `%s` = `booldict[onshell]`: `0` (None / cascade), `1` (True / comma-decay), `2` (False / `$`-forbidden).
- One line per s-channel vertex per config: `for iconf, config in enumerate(s_and_t_channels): for vertex in config[0]:` (:5886-5894). `config[0]` is the s-channel list.

## Confirmed probe (parse-time, MG5_aMC v3.7.1)
`generate p p > t t~, t > b w+, w+ > e+ ve; output` →
`SubProcesses/P1_gg_ttx_t_bwp/decayBW.inc`:
```
      DATA GFORCEBW(-1,1)/1/
      DATA GFORCEBW(-2,1)/0/
      DATA GFORCEBW(-1,2)/1/
      DATA GFORCEBW(-1,3)/1/
```
Interpretation: the comma-decayed mother legs (`t`, `w+`) → `/1/` (onshell=True). The leg whose s-channel is not a comma-decay product → `/0/` (onshell=None). Confirms the booldict mapping end-to-end at runtime. Leg numbers are negative (internal); the same leg `-1` appears across iconfigs 1,2,3.

## Contrast probe — flat (forgot-parens) nested subdecay discards a forced-BW line
`generate p p > t t~, t > b w+, w+ > e+ ve; output` (FLAT, no parens around the w+ subdecay) → MG5_aMC v3.7.1 emits the RED "Decay without corresponding particle... w+ is discarded" warning (diagram_generation.py:1409-1414) and DROPS the `w+ > e+ ve` subdecay. Resulting `SubProcesses/P1_gg_ttx_t_bwp/decayBW.inc`:
```
      DATA GFORCEBW(-1,1)/1/
      DATA GFORCEBW(-2,1)/0/
      DATA GFORCEBW(-1,2)/1/
      DATA GFORCEBW(-1,3)/1/
```
The `t` mother (-1) still gets /1/ (t IS a comma-decayed core final-state leg), but there is NO additional forced-BW line for an internal `w+` because that subdecay was discarded. Compare with the nested correct-syntax probe above (`t > b w+, w+ > e+ ve` properly parenthesised) where the w+ mother also carried /1/. So: flat-vs-nested syntax changes which legs get gForceBW=1, and the flat form silently (after a warning) drops a forced-BW channel. Always confirm against decayBW.inc rather than counting commas.

## Comma form vs arrow form — same final state, different gForceBW (chain-decay origin of the cut_decays seam)
The comma decay form and the cascade-arrow form produce the SAME final-state leaves
but write DIFFERENT gForceBW, because only the comma form marks the resonance as an
explicit decaying mother (`onshell=True`). Probe (MG5_aMC v3.7.1):
- **Comma** `p p > z, z > e+ e-; output` → `SubProcesses/P1_qq_z_z_ll/decayBW.inc`:
  `DATA GFORCEBW(-1,1)/1/` — the Z s-channel mother is forced-BW (comma-decay onshell=True).
- **Arrow** `p p > z > e+ e-; output` → `SubProcesses/P1_qq_ll/decayBW.inc`:
  `DATA GFORCEBW(-1,1)/0/` — the Z is an ordinary cascade propagator (onshell=None).
The subprocess NAME also differs: comma → `P1_qq_z_z_ll` (Z written as an explicit
decaying resonance, the `_z_` segment), arrow → `P1_qq_ll` (no resonance segment). This
is the chain-decay-side mechanism: the comma syntax is what records the Z as a decaying
resonance, which (a) writes gForceBW=1 here, and (b) downstream tags the daughter leptons
as **decay products** (`from_decay`).

**The cut_decays seam (NOT walked here — name only).** Because the comma form's daughters
are decay products, the cut machinery tags them `from_decay`; with the default
`cut_decays=False` those legs are EXEMPT from per-particle parton-level cuts, while the
arrow form's leptons (gForceBW=0, not decay products) ARE cut. The cut-application
mechanism and the σ consequence are bw-window / kinematic-cuts territory — this slice
establishes ONLY that the comma syntax is what marks the leptons as decay products
(gForceBW=1, `_z_` resonance subprocess). Anchored observation (not verified in
this slice): arrow σ=1131 pb (cuts apply) vs comma σ=2840 pb (cuts
silently inert), same single-graph ME (NGRAPHS=1, JAMP(1,1)=AMP(1)) — the σ gap is a
cut-application difference, NOT an amplitude difference; the two `matrix1_orig.f` differ
only in HELAS wavefunction-build order (comma builds Z from final leptons, arrow from
initial quarks) — evaluation order, not physics. (The single-graph NGRAPHS=1 anchor is a
specific qq̄ subprocess; the `p p` probe above enumerates multiple flavour channels, so
its top-line diagram count is not 1 — the gForceBW=1-vs-0 contrast is what this slice owns.)

## Dependency on configs.inc / s_and_t_channels
`write_decayBW_file` is fed the same `s_and_t_channels` object that `write_configs_file` produces (export_v4.py:4453, then 4474-4476). That object is built from `get_s_and_t_channels` on each Helas diagram (export_v4.py:~5462). So decayBW.inc and configs.inc share the per-channel s/t-channel decomposition; the gForceBW leg numbering matches the s-channel mother numbering in configs.inc for the same iconfig. The emission "relies on" configs.inc's channel data in the sense that both read the same s_and_t_channels list in lock-step.

## Downstream consumers (out of this slice — name only)
- BW-window enforcement at run time (`myamp.f`) reads gForceBW — bw-window slice.
- Phase-space integrator channel-mapping reads gForceBW — phase-space slice.
This slice only establishes what integer gets WRITTEN, not what it DOES at run time.

## NOT this slice: chain-σ normalization by the param-card total width
A recurring question frames "the param_card total width is the chain-σ BR denominator;
a stale `DECAY <pdg>` silently inflates σ by Γ_correct/Γ_stale, BR≫1 unflagged" as something
to fold into a chain-decay page. **This is out of slice.** The comma syntax (this
slice) only decides WHICH s-channel mother is marked a decaying resonance (onshell=True →
gForceBW=1, `_h_`/`_z_` resonance subprocess segment). It does NOT read, store, or divide
by the total width. The σ normalization is the **Breit-Wigner propagator denominator**:
the total width enters the generated Fortran ME as `MDL_W<particle>` read from the
param-card at run time (with `small_width_treatment`, matrix_madevent_v4.inc:259-260),
inside the HELAS propagator wavefunctions. The partial-width numerator comes from the
decay sub-ME. Both the BR-factor denominator and the production-side resonance propagator
width are matrix-element / phase-space territory, NOT the parser / onshell / decayBW
emission layer. Route width-normalization questions to phase-space (and madwidth for the
width VALUE itself). gForceBW=1 picks the propagator to BW-sample; it carries no width.
