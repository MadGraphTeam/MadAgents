---
description: Provenance split — gForceBW is a static decayBW.inc data array (from decay-chain onshell flag); lbw is set at RUNTIME by base-3 DeCode in madevent_driver.f, NOT in decayBW.inc; LO-onshell vs NLO-from_group writer divergence. Also: single-$ (forbidden_onsh_s_channels) KEEPS the diagram and sets onshell=False→gForceBW=2 + ALOHA P1D/BWCUTOFF propagator (vs $$ which REMOVES the diagram); the $-subtraction math is ALOHA's slice, bwcutoff only supplies the VALUE
---

# gForceBW vs lbw — provenance split (decay-chains consumer)

Both arrays drive the LO `cut_bw` / `set_peaks` BW machinery (bw-onshell-test-cutbw.md), and
the role card lists "decayBW.inc — provides the gForceBW and lbw arrays". That last clause is
**wrong**: `decayBW.inc` carries `gForceBW` ONLY. `lbw` has a completely different origin.
Verified by reading a built `decayBW.inc` + the writers, v3.7.1.

## gForceBW — static `data` array in decayBW.inc, from the decay-chain `onshell` flag
- **Writer:** `$MADGRAPH_INSTALL/madgraph/iolibs/export_v4.py:5879` `write_decayBW_file`. For
  each s-channel vertex it emits `data gForceBW(<leg.number>,<iconf+1>)/<code>/`
  (export_v4.py:5892-5894) with `booldict = {None:"0", True:"1", False:"2"}` (:5884) over
  `leg.get('onshell')`.
- **The `onshell` flag semantics** (the decay-chain encoding source-of-truth):
  `$MADGRAPH_INSTALL/madgraph/core/base_objects.py:2111` (v3.7.1, single line, re-read):
  *"onshell: decaying leg (True), forbidden s-channel (False), none (None)"*. So:
  - decay-chain `decay` syntax (a decaying parent) → `onshell=True` → **gForceBW=1** (forced on-shell).
  - **single-`$`** forbidden-*onshell*-s-channel syntax (`forbidden_onsh_s_channels`) →
    `onshell=False` → **gForceBW=2** (on-shell forbidden). See the `$` vs `$$` section below.
  - ordinary internal propagator → `onshell=None` → **gForceBW=0** (no force).
  This is the exact 0/1/2 encoding the LO consumer (myamp.f:64 `integer gForceBW`) reads.

## `$` (forbidden_onsh_s_channels) vs `$$` (forbidden_s_channels) — the onshell=False source is `$`, NOT `$$`
**Correcting an earlier claim on this page** that attributed `onshell=False`/gForceBW=2 to `$$`.
Source-walked v3.7.1; the two operators diverge at diagram generation:
- **Double-`$$` (`forbidden_s_channels`) REMOVES the diagram.**
  `$MADGRAPH_INSTALL/madgraph/core/diagram_generation.py:742-775`: the list-comprehension drops
  any diagram whose non-final vertex `get_s_channel_id` is in `forbidden_s_channels` (`ninitial==2`
  fast path :745-751; the asymmetric reverse-scan for `ninitial!=2` :753-775). The diagram is
  GONE — no leg survives to carry any onshell flag. `$$` therefore produces **no** gForceBW entry
  for that channel (the topology no longer exists).
- **Single-`$` (`forbidden_onsh_s_channels`) KEEPS the diagram, marks the leg.**
  `diagram_generation.py:781-793`: for each surviving s-channel vertex whose id is in
  `forbidden_onsh_s_channels`, it pops the last leg and `newleg.set('onshell', False)` (:792),
  comment *"Use onshell = False to indicate that this s-channel is forbidden"*. The diagram stays
  in the amplitude; only its propagator leg is flagged `onshell=False`.
- That `onshell=False` is the SINGLE source feeding BOTH downstream artefacts:
  1. `export_v4.py:5894` → `booldict[False]="2"` → **gForceBW=2** in `decayBW.inc`.
  2. `helas_objects.py:1597-1600` → `output['bwcutoff']='BWCUTOFF,'` (extra routine arg) +
     `helas_objects.py:1898` → `tags.append('P1D')` (`D`=DOLLAR) — this is what makes the ALOHA
     routine name carry `P1D` (e.g. `FFV2_5P1D_3`). NOTE `helas_objects.py:1593-1594` is a
     commented-out abandoned alternative (`W = width*BWCUTOFF`); the LIVE path keeps the real
     width and instead passes BWCUTOFF as a separate denominator arg.
- **The propagator math is ALOHA-generated, NOT myamp.f.** `aloha/aloha_writers.py:241` appends
  `BWCUTOFF` to the routine call args only when `'P1D' in self.tag`; `aloha_writers.py:736` lists
  `bwcutoff` among the global names (alongside `pi`,`g`,`as`) so it is recognised as a model
  parameter, not prefixed. The denominator object is `aloha/aloha_object.py:1650`
  `DenominatorPropagator`. The on-shell-region treatment of the kept `$` propagator therefore
  lives in ALOHA's generated `P1D` routine — `myamp.f`'s `cut_bw` `bwcutoff*Γ_eff` window is a
  SEPARATE mechanism. The shared element is only the `bwcutoff` VALUE (run.inc:37
  `common/to_bwcutoff/`, this slice's run-card knob).
- **banner.py side-effect:** `$MADGRAPH_INSTALL/madgraph/various/banner.py:5058` forces
  `self['sde_strategy']=1` whenever any proc has `forbidden_onsh_s_channels` set (comment
  :5055 *"forbid to use sde_strategy=1 with $ syntax"* — actually forces it TO 1).
- **Built-file confirmation (multi-process / multi-config):** every built
  `decayBW.inc` contains ONLY `DATA GFORCEBW(<leg>,<iconfig>)/<code>/` lines — **no lbw, no
  other symbol**. The second index is **iconfig** (per-topology config), not a second leg.
  - Full forced chain `t > w+ b, w+ > l vl`
    (`P1_qq_ttx_t_qwp_wp_lvl_tx_qwm_wm_lvl`): five lines, forced legs `GFORCEBW(-1..-4,1)/1/`
    (decayed t + sub-resonances), un-decayed leg `GFORCEBW(-5,1)/0/`.
  - Partial chain `h3 > l l` with spectator (2HDM, `P1_bbx_h3_h3_llh1`): **two configs** —
    `GFORCEBW(-1,1)/0/ GFORCEBW(-2,1)/1/` and `GFORCEBW(-1,2)/0/ GFORCEBW(-2,2)/1/`. The
    forced h3 resonance is `1` across BOTH configs; the spectator/non-resonant leg is `0`.
    This is the key sample for the iconfig axis: a forced leg keeps gForceBW=1 in every
    config of its topology.
  - No decay chain `g g > t t~` (`P2_gg_ttx`): `GFORCEBW(-1,1)/0/ GFORCEBW(-1,2)/0/` — every
    leg `0` (onshell=None for all internal props), so all legs run the default non-forced
    window (5σ in Regime B). Confirms: no chain-decay syntax ⇒ no gForceBW=1 anywhere.
- **Declared `integer`** in every LO consumer: myamp.f:64/248, setcuts.f:981,
  madevent_symmetry.f:180/323. Filled by the `decayBW.inc` data statements at compile time
  (static per process directory).

## gForceBW=0 for intermediate propagators: which bwcutoff sites apply
Two valid setups for the SAME light-Higgs H→WW(*)→ττνν physics differ in whether the W's
are forced, and therefore in which bwcutoff-gated sites are active for them:
- **Chain form** `(h > w+ w-, w+ > ta+ vt, w- > ta- vt~)` — each `w+`/`w-` is a decaying
  parent in the decay chain → `onshell=True` (base_objects.py:2111) → **gForceBW=1** in
  `decayBW.inc` (export_v4.py:5894, booldict[True]="1"). The W's enter ALL six bwcutoff
  sites (Regime A + Regime B, bw-bwcutoff-scaling-regimes.md) — **`bwcutoff` is load-bearing**
  for the W's (size per bw-cutoff-sizing-derivation.md; the registered default → `Impossible BW
  configuration` for sub-threshold).
- **4-body form** `h > ta+ vt ta- vt~ / ta+ z` — the H decays directly to a 4-fermion final
  state; the intermediate W's are **ordinary internal propagators**, NOT decay-chain parents
  → `onshell=None` → **gForceBW=0**. (WHICH syntax yields onshell=None is chain-decay's slice;
  here we consume the resulting gForceBW=0.)
- **Regime A sites (UNCONDITIONAL)** — bwcutoff scales these for **ALL** legs, gForceBW=0 or
  not: Les-Houches on-shell tag (myamp.f:136-139, window `bwcutoff·Γ_eff`), and s-hat
  1/s-vs-BW transform gate (myamp.f:575, bwcutoff in `smin/stot > spole + bwcutoff*swidth`).
  **bwcutoff gates the BW window regardless of gForceBW status.**
- **Regime B sites (FORCED-ONLY)** — cut_bw enforcement onshell (myamp.f:188-193), set_peaks
  grid lower bound (myamp.f:402-409), impossible-onshell guard (myamp.f:419-422): these use
  a **hardcoded 5σ** window (`5d0*prwidth_tmp`) when gForceBW=0, not `bwcutoff` (Regime B,
  bw-bwcutoff-scaling-regimes.md). The off-shell-cut branch at myamp.f:179
  (`else if (gForceBW(i, iconfig).eq.1) then ... cut_bw=.true.`) is SKIPPED for gForceBW=0
  legs. **The window is different (5σ instead of bwcutoff), not inert.**
- **Sizing implication for 4-body H→WW(*)**: the W propagators still carry the physical BW
  shape; Regime A bwcutoff gates the Les-Houches tagging window and s-hat transform for them.
  Regime B uses 5σ. For the **two-body kinematic floor** of a 4-body decay ME (m_parent -
  m_daughter as the minimum W invariant mass when the partner is on-pole), the required
  bwcutoff at the window layer is `(m_daughter − (m_parent − m_daughter)) / Γ_daughter` —
  the distance from the pole down to the two-body kinematic floor, in units of Γ_daughter.
  This is a specific instance of the general `(m_pole − virtuality_floor)/Γ_eff` formula,
  where the virtuality floor is the two-body constraint rather than the daughter's own
  decay-product mass (which applies to explicit chain-decay sub-decays).

## lbw — RUNTIME base-3 DeCode in madevent_driver.f, NOT in decayBW.inc
- `lbw(0:nexternal)` lives in `common /to_BW/ lbw` (myamp.f:50-51, cuts.f:118-119,
  madevent_driver.f:268-269). It is **never written by any data statement / decayBW.inc**.
- Set at runtime in `$MADGRAPH_INSTALL/madgraph/iolibs/template_files/madevent_driver.f`
  `get_user_params` from the requested configuration number `dconfig` (read at :330):
  - `ncode=int(dlog10(3d0)*(max_particles-3))+1` (:332) — number of **base-3** digits for the
    BW code.
  - `iconfig=int(dconfig*(1+10**(-ncode)))` (:333) — integer part = the channel.
  - `dconfig-iconfig` is the fractional BW sub-config code. If 0: `lbw(0)=0`, prints
    *"Not subdividing B.W."* (:340-342). Else `lbw(0)=1`,
    `jconfig=dconfig*(10**ncode+0.1)` (:345) then
    **`call DeCode(jconfig,lbw(1),3,nexternal)`** (:347) — unpacks `jconfig` into
    `lbw(1..nexternal-2)` as **base-3 digits** (the `3` arg). Each digit is 0/1/2 →
    matches the lbw encoding **0=no cut / 1=require-BW / 2=exclude** (myamp.f:88-94, 196-198).
  - `DeCode` is a generic base-N unpacker: `$MADGRAPH_INSTALL/Template/LO/Source/basecode.f:60`
    `subroutine DeCode(icode,iarray,ibase,imax)`, doc *"icode = Sum[ iarray(k) * ibase^k ]"*.
    Called with `ibase=3` here; the base-3 alphabet {0,1,2} is exactly the lbw cut-direction
    encoding (same file holds `Encode`, the inverse, used by madevent_symmetry/Encode at :427).
- => `lbw` is the **per-channel BW-subdivision request**, chosen at survey/refine time by the
  integration driver, NOT a property of the process topology. The same `decayBW.inc`/process
  can run with different `lbw` settings across sub-configs. (WHY a channel is subdivided into
  require/exclude variants is phase-space/integration territory; the lbw *array semantics* and
  its runtime origin are this slice.)

## The two arrays are orthogonal axes into cut_bw
- **gForceBW** (static, per leg, from decay-chain syntax) selects the **window scale**:
  gForceBW=1 → `bwcutoff*Γ_eff`; else → `5d0*Γ_eff` (Regime B, myamp.f:188-194;
  bw-bwcutoff-scaling-regimes.md). gForceBW=2 → hard-cut forbidden s-channel (sde_strat=1).
- **lbw** (runtime, per channel) selects the **direction of the cut**:
  lbw=1 require-on-shell (off-shell fails), lbw=2 exclude (on-shell fails) (myamp.f:196-198).
- A decay-chain forced leg can therefore be tested with the bwcutoff window (from gForceBW=1)
  AND a require/exclude direction (from lbw) independently — they are set by different
  machinery at different times.

## NLO writer divergence (refines bw-nlo-window-sites.md)
- `export_fks.py:3966` ALSO writes `data gForceBW(...)` lines — but over
  `booldict[leg.get('from_group')]` (NOT `onshell`), and declares
  **`logical gforceBW`** (export_fks.py:3979), not `integer`. It is bundled into a
  configs-style file (with mapconfig/iforest/sprop), not a standalone `decayBW.inc`.
- **No NLO Fortran consumes it:** `grep -rn gForceBW Template/NLO/` = 0. The NLO BW-window
  sites (cluster.f:692, add_write_info.f:808; bw-nlo-window-sites.md) test a plain
  `bwcutoff*real_width` for ALL resonances and never read gForceBW. So: a gForceBW array IS
  *emitted* at NLO output, but with `from_group` (boolean) semantics, logical type, and **no
  consumer** — the forced-on-shell apparatus is functionally LO-only even though the symbol
  is written. (My earlier "no gForceBW at NLO" was right about the BW-window behaviour, but
  the symbol is emitted by the exporter.)

## Cautions
- Do NOT say "decayBW.inc provides lbw" — it provides gForceBW only; lbw is runtime
  (madevent_driver.f DeCode). Mixing them up mis-locates where a require/exclude BW setting
  comes from.
- The `ncode`/base-3 detail means lbw digit count and dconfig fractional encoding scale with
  `max_particles-3`; a static read of decayBW.inc tells you nothing about lbw.
- Static source facts (writers, encodings, built-file content, grep absences — all confirmed).
  The per-channel lbw value a given survey assigns is a runtime quantity (not
  probed here; it is set inside the integration driver).
- Do NOT attribute `onshell=False`/gForceBW=2 to `$$`. `$$`
  (`forbidden_s_channels`) REMOVES the diagram (diagram_generation.py:742-775); the single-`$`
  (`forbidden_onsh_s_channels`) is what KEEPS it and sets `onshell=False`
  (diagram_generation.py:792). See the `$` vs `$$` section.
- The `$`-propagator's on-shell-region treatment is **ALOHA-generated** (`P1D` routine,
  aloha_object.py:1650 / aloha_writers.py:241), NOT a `myamp.f` `bwcutoff*Γ_eff` window. This
  slice owns the `bwcutoff` VALUE (run.inc:37) consumed by that routine and the gForceBW=2
  entry — the propagator math itself is ALOHA's slice. Don't claim myamp.f computes the
  `$`-subtraction.
