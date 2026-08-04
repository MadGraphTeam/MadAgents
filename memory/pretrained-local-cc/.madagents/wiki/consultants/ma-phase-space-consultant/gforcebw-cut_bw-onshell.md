---
description: gForceBW (decayBW.inc) semantics and the cut_bw/OnBW per-event accept-reject in myamp.f — how forced/excluded BWs gate events and feed LesHouches on-shell flags.
---

# gForceBW, cut_bw, and the OnBW on-shell test

## decayBW.inc / gForceBW — where forced-BW flags come from
`<P>/decayBW.inc` fills `gForceBW(-max_branch:-1, lmaxconfigs)` (declared in both myamp.f:64 and
set_peaks myamp.f:248). Per-leg `-i`, per-config:
- `0` = no forcing (ordinary BW, e.g. an s-channel resonance from `generate p p > z`).
- `1` = forced on-shell (decay-chain syntax `> z >`; the resonance MUST be on its BW).
- `2` = forced off-shell / forbidden on-shell (on-shell contribution removed).

Concrete shapes:
- `q q~ > z > z > l+ l-` (`<PROC_DIR>/.../P1_qq_z_z_ll/decayBW.inc`): `GFORCEBW(-1,1)/1/`
  — the single decay-chain Z is forced.
- WBF `q q > h q q` (`<PROC_DIR>/.../P1_qq_hqq/decayBW.inc`): only `GFORCEBW(-1,4)/0/`,
  `(-2,4)/0/`, `(-1,6)/0/`, `(-2,6)/0/` — sparse: entries appear only for configs/legs that have an
  s-channel BW-capable propagator; t-channel-only configs (1,2,3,5) get no entry. NOT forced (=0).
- Two-level cascade `p p > t t~, (t > b w+, w+ > e+ ve), (t~ > b~ w-, w- > j j)`
  (`<PROC_DIR>/.../P1_gg_ttx_t_bwp_wp_lvl_tx_bxwm_wm_qq/decayBW.inc`):
  config 1 (s-channel gg production diagram) emits FIVE entries `GFORCEBW(-1..-4,1)/1/` (the four
  decay resonances W-/t~/W+/t, all forced) plus `GFORCEBW(-5,1)/0/` (the production gluon s-channel,
  PDG 21 in `SPROP(-5,1)/21/` — ordinary, None->0). Configs 2,3 (t-channel production: `TPRID(-5)/6/`,
  `TPRID(-6)/21/`) emit only FOUR entries `(-1..-4)/1/` — no `-5` entry, because the production side
  is t-channel and the s-channel-only writer loop skips it. So the production propagator carries
  gForceBW=0 ONLY when it is an s-channel (the gg fusion diagram); when production is t-channel it
  gets no decayBW entry at all. This is the canonical "every decay resonance forced, production not"
  shape from a `>` cascade.

decayBW.inc is also read by gensym (madevent_symmetry.f:181) for the BW-subdivision conflict logic.

## Output-side: where the 0/1/2 values come from (write_decayBW_file)
The runtime 0/1/2 above is the direct image of each s-channel leg's `onshell` flag, written at
`output` time. `write_decayBW_file` (`$MADGRAPH_INSTALL/madgraph/iolibs/export_v4.py:5879`, ME class):
- `booldict = {None: "0", True: "1", False: "2"}` (export_v4.py:5884) — the exact mapping.
- It loops `s_and_t_channels`, and for each config only over the **s-channels** (`config[0]`,
  export_v4.py:5886-5887), emitting `data gForceBW(<leg number>,<iconf+1>)/<bool>/`
  (export_v4.py:5892-5894) for the resulting (last) leg of each s-channel vertex. T-channel vertices
  are NOT iterated => no gForceBW entry => explains the sparse, t-channel-free decayBW.inc.
The leg `onshell` flag semantics (base_objects.py:2111-2112 comment):
"onshell: decaying leg (True), forbidden s-channel (False), none (None)". Set during diagram
generation:
- **True -> gForceBW 1** (forced on-shell): a leg whose id is in `decay_ids`, i.e. it has a decay
  chain from the `>` decay-chain syntax (`diagram_generation.py:1286,1299`).
- **False -> gForceBW 2** (forbidden on-shell): a leg in `forbidden_onsh_s_channels`, i.e. the `$`
  forbid-on-shell process syntax (`diagram_generation.py:790-793`).
- **None -> gForceBW 0** (ordinary): the default (`base_objects.py:2112`).
So the whole chain is: process syntax (`>` / `$` / plain) -> leg.onshell (True/False/None) -> booldict
-> gForceBW(leg,config) -> cut_bw gate. The `>`-vs-`$` syntax itself borders the process-syntax slice;
the leg-flag -> gForceBW image (this writer) is mine.

## cut_bw (myamp.f:2) — per-event accept/reject
Called per phase-space point. Walks propagators of `this_config`, reconstructs each branch
4-momentum, and for width>0 s-channel branches (myamp.f:115-203):
- Computes `xmass=sqrt(p^2)` and the on-shell test
  `onshell = |xmass-prmass| < bwcutoff*prwidth_tmp  AND  (width/mass < <hardwired narrow-resonance ratio>
  OR gForceBW==1)` (read the ratio literal at myamp.f:136-139).
  `prwidth_tmp=max(prwidth, prmass*small_width_treatment)` (myamp.f:131-132).
- **gForceBW==2 + sde_strat==1 + onshell** -> `cut_bw=.true.` (reject): removes on-shell-forbidden
  s-channels (myamp.f:142-145).
- **gForceBW==1 + .not.onshell** -> `cut_bw=.true.` (reject): forced resonance must be on its BW
  (myamp.f:179-184).
- Sets `OnBW(-i)` (common `/to_BWEvents/`) for LesHouches, with identical-particle deduplication so
  only one of two same-PDG resonances is flagged (myamp.f:146-178).
- The `lbw(nbw)` array (from the dconfig BW-subdivision code) gives a second gate: `onshell &&
  lbw==2` or `.not.onshell && lbw==1` -> reject (myamp.f:196-200). This routes each event to the
  matching BW sub-channel.

`OnBW` and the LesHouches on-shell-mass reshuffling feed event writeout; `cut_bw=.true.` discards
the point from the channel's integral.

## sde_strat — single-diagram-enhancement strategy switch
Common `/TO_CHANNEL_STRAT/tmin_for_channel, sde_strat`. `sde_strat==1` = standard single-diagram
enhancement; `sde_strat==2` = approximate by the propagator denominator (used by get_channel_cut,
genps.f:1931,1945). The gForceBW==2 reject only fires under `sde_strat==1` (myamp.f:142).

## Cautions
- Two distinct on-shell tests live in cut_bw: the LesHouches one (bwcutoff window, myamp.f:136) and a
  phase-space one recomputed at myamp.f:188-194 (`bwcutoff*width` if forced, else a hardwired multiple
  of width — read myamp.f:188-194). They serve different purposes; don't conflate.
- The exact `bwcutoff` window semantics / run_card default are the **bw-window slice's** territory; I
  cite bwcutoff only as the variable cut_bw multiplies.
- gForceBW is read from decayBW.inc which is generated from the decay-chain syntax at output — a plain
  `generate p p > z, z > l+ l-` vs `generate p p > z > l+ l-` can differ in whether the Z is forced.
