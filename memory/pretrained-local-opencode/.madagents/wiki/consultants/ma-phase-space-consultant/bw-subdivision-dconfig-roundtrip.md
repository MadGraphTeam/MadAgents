---
description: The base-3 dconfig BW-subdivision code is one encoding that round-trips output→survey→driver→runtime under a shared ncode digit-count contract; one digit per conflicting-BW leg gates on/off/either-shell.
---

# BW-subdivision dconfig code: the four-stage round-trip invariant

A process whose diagram has multiple resonances that cannot all be on-shell at once (BW
*conflict*) has each surviving ICONFIG split into BW sub-channels. The split is carried by ONE
base-3 fractional code that round-trips through four stages. The instance pages each describe a
single touch-point; this page names the invariant that ties them, which holds for every
BW-conflict process — not just the three examples.

## The single contract: ncode digit count
`ncode = int(dlog10(3d0)*(max_particles-3))+1` computed **identically** at two sites:
- survey: `$MADGRAPH_INSTALL/madgraph/iolibs/template_files/madevent_symmetry.f:196`
- driver: `$MADGRAPH_INSTALL/madgraph/iolibs/template_files/madevent_driver.f:332`
If these two formulas ever diverge the encode/decode silently desyncs. `max_particles` is the
per-process `maxparticles.inc` value (NOT nexternal). Probe: `P1_qq_zh_z_ll_h_ttx_t_bwp_tx_bxwm`
has `max_particles=8` -> `int(0.477*5)+1 = 3` digits; symfact.dat carries `1.171`, `1.180`
(3 fractional digits), confirming the formula.

## The single alphabet: base-3, one digit per conflicting BW leg
`EnCode`/`DeCode` (`$MADGRAPH_INSTALL/Template/LO/Source/basecode.f:29,60`) are exact inverses:
`icode = Sum[iarray(k)*3^(k-1)]`, `iarray(k) in {0,1,2}`. One array slot per (potentially
conflicting) propagator. Per-digit semantics, set by the runtime lbw gate (myamp.f:196-200):
- digit/`lbw==0`: leg not subdivided — no on-shell gate applied.
- digit/`lbw==1`: this sub-channel requires the leg **off-shell** (reject if on-shell).
- digit/`lbw==2`: this sub-channel requires the leg **on-shell** (reject if off-shell).
So the code partitions phase space so each surviving resonance is on-shell in exactly one
sub-channel and the impossible all-on-shell combinations are dropped.

## The four stages
1. **Enumerate (survey)** — madevent_symmetry.f `write_bash`: `BW_Conflict` (286) flags conflicting
   legs; `bw_increment_array`+`enCode` (226,265) walk base-3 codes; `failConfig` (434) drops
   impossible combos; each survivor emits `dconfig=mapconfig(i)+icode*1d0/10**ncode` (243/261) into
   symfact.dat. Covered by iconfig-channel-structure.md.
2. **Decode (driver)** — get_user_params: `iconfig=int(dconfig*(1+10**(-ncode)))` (driver.f:333)
   peels the integer config; `jconfig=dconfig*(10**ncode+0.1)` (345); `DeCode(jconfig,lbw(1),3,
   nexternal)` (347) fills lbw. `lbw(0)=0` => not subdividing. Covered by
   driver-and-channel-selection-sampling.md.
3. **Surface on disk (driver)** — open_file_local (driver.f:366,420-435): `G<mincfig>` if
   `lbw(0)==0`, else `G<mincfig>.<jconfig>` (jconfig re-`Encode`d at 427). So a conflict config
   yields multiple G-dirs for ONE MAPCONFIG. Probe: G1.171, G1.180 both present on disk for the
   zh_tt process above.
4. **Gate events (runtime)** — myamp cut_bw: the lbw alphabet above rejects mismatched points
   (myamp.f:196-200), routing each event to its matching sub-channel. Covered by
   gforcebw-cut_bw-onshell.md.

## Why this is more than the union of the instance pages
The instances each describe their local read/write of `dconfig`/`lbw`. The load-bearing facts that
no single page owns: (a) the ncode formula is a *shared contract* across two files; (b) the per-digit
base-3 alphabet is the SAME object that survey enumerates, driver decodes, and myamp gates on; (c)
the count of `G<m>.<jconfig>` dirs equals the number of non-failing base-3 codes for that config.
Apply this to ANY conflict process to predict its sub-channel count and G-dir layout, even ones the
instance pages never named.

## The conflict CRITERION: daughter-mass exceeds pole-mass (intra-branch)
`BW_Conflict` (`$MADGRAPH_INSTALL/madgraph/iolibs/template_files/madevent_symmetry.f:286`) does NOT
flag a leg as conflicting just because two resonances coexist. The actual test
(madevent_symmetry.f:368-376) walks the propagator chain accumulating `xmass(-i) =
xmass(daughter1)+xmass(daughter2)`, and sets `lconflict(-i)=.true.` ONLY when
`prwidth(-i)>0 .and. xmass(-i) .gt. prmass(-i) .and. iden_part(-i).eq.0` — i.e. the propagator's
decay products are already heavier than its own pole mass, so it physically *cannot* sit on its
resonance. This is an **intra-branch** accumulation (xmass sums daughter masses up a single chain);
two resonances in disjoint branches never enter a common conflict. (Plus a global fallback at :411:
if `stot < mtot**2`, all BWs marked conflicting — not-enough-energy case.)
- Consequence: a **clean cascade** where every parent is heavier than the sum of its decay daughters
  has NO conflict and NO subdivision, regardless of how many resonances are simultaneously forced.
  Probe `p p > t t~, (t > b w+, w+ > e+ ve), (t~ > b~ w-, w- > j j)` — four forced BWs
  (t,t~,W+,W-; decayBW.inc all `/1/`), but t(MT=173) > b+W(~85) and W(MW=80) > e+ve(~0), so
  `xmass(-i) < prmass(-i)` everywhere -> no conflict expected. props.inc confirms the pole masses
  (PRMASS(-2)=MDL_MT, PRMASS(-1)=MDL_MW). The t/t~ pair in disjoint branches cannot co-conflict by
  construction. (HYPOTHESIS on the runtime symfact.dat: not verifiable from `output` alone — see
  caution below.)

## Cautions / boundaries
- "Conflict" detection (`BW_Conflict`) and `failConfig`'s drop rule are survey-side; the *width of
  the on-shell window* used in the lbw gate (`bwcutoff` vs `5*width`) is the **bw-window slice's**.
- **symfact.dat is a SURVEY artefact, not an output artefact.** `output` alone does NOT write
  symfact.dat (confirmed absent in both P-dirs of the chain probe above); gensym writes it during
  `launch`/survey. So the *final* subdivision outcome (fractional dconfig codes) cannot be read off a
  bare `output` dir — only the conflict CRITERION (source + configs.inc/props.inc) is statically
  determinable. To verify the no-subdivision prediction empirically you must `launch` (survey).
- How many VEGAS points each sub-channel gets is the **numerical/VEGAS slice's**; this page owns the
  channel partition, not its sampling budget.
- No conflict => no subdivision: symfact.dat shows plain `1  1`, single `G<m>` dir, lbw(0)=0
  (probe: dy_chain_decay P1_qq_z_z_ll).
