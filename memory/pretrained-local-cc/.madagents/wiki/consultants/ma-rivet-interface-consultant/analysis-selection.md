---
description: RivetCard.getAnalysisList — [default] sentinel semantics, the MC_* curated set, Contur beam-energy gating, rivet_sqrts, and setWeightName for merged samples.
---

# Analysis selection (RivetCard.getAnalysisList) + weight name

`RivetCard(ConfigFile)` at `$MADGRAPH_INSTALL/madgraph/various/banner.py:1563`.

## Defaults (default_setup, 1565-1588)
- `analysis = []` (typelist=str), `run_rivet_later=False`, `run_contur=False`, `draw_rivet_plots=False`, `draw_contur_heatmap=True`.
- heatmap axes: `xaxis_var/relvar/label="default"`, `*_log=False`; same for y.
- HIDDEN (1581-1588): `contur_ra="default"`, `rivet_sqrts="default"`, `weight_name="default"`, `rivet_add="default"`, `contur_add="default"`.

NOTE the template `rivet_card_default.dat` ships `analysis = [default]` (literal token `default`), but `default_setup` initialises `analysis=[]`. The sentinel branch handles `"default"`, `None`, and `""` identically.

## getAnalysisList(runcard) (1650-1694)
- `rivet_sqrts = int(ebeam1)+int(ebeam2)`; stored in `self["rivet_sqrts"]` as str (1659-1660).
- If `len(analysis)==1` and that element is `"default"`/`None`/`""` (1662-1665):
  - `run_contur=False` => curated MC set in order: `MC_ELECTRONS, MC_MUONS, MC_TAUS, MC_MET, MC_JETS` (1667-1671).
  - `run_contur=True` (1672-1685):
    - Requires `lpp1==1 and lpp2==1` (proton-proton) else MadGraph5Error "Incorrect beam type" (1673-1674).
    - Gates on the hardcoded `ebeamsLHC` per-beam energy set at banner.py:1675 — read the list fresh; it encodes the standard LHC pp beam energies.
    - Both ebeams in that set AND equal -> appends `$CONTUR_RA{sqrts/1000}TeV`, sets `contur_ra="{N}TeV"` (1677-1680).
    - ebeams unequal -> MadGraph5Error; ebeams not in the LHC list -> MadGraph5Error (1681-1685).
- `len(analysis)==1` real name -> that single analysis (1687-1688).
- `len(analysis)>1` -> each element verbatim (1690-1692). No `[default]` mixing in the multi-element branch.

So `[default]`+contur is locked to the standard LHC pp beam energies enumerated in `ebeamsLHC` (banner.py:1675, read the list fresh), equal-beam only. Other energies with `[default]`+contur raise.

## read (1590-1618)
- Comment stripping: `#` branch splits on `#` (1601-1602); the `!` branch ALSO splits on `#` (1605, source bug — `!`-comments are NOT stripped). `key=value` lines split on first `=`.
- For `xaxis_var/relvar/label`, `yaxis_*`, `rivet_add`, `contur_add`: value lowercased; if `=="default"` -> set to `""` (1612-1617). (`analysis`, `rivet_sqrts`, `weight_name`, `run_contur` NOT in this list.)

## write (1620-1648)
- Template-driven; rewrites each `k = v` from current value, keeps trailing comment; logs "Adding missing parameter ... (with default value)" for template keys not in self.

## setWeightName(runcard, py8card) (1696-1706)
- Only acts if `weight_name=="default"`.
- `ickkw==0` (no merging) => `weight_name="None"` (string) (1703-1704).
- else => `"Weight_MERGING={qCut}"` from `py8card['JetMatching:qCut']` via `round()` (banner.py:1705-1706 carries the dp count — read fresh).
  - CAUTION: source reads `.str(round(...))` — `float.str` is not a method; line raises AttributeError if reached. Probe-candidate: does a merged (ickkw!=0) Rivet run crash here? HYPOTHESIS until probed.

## rivet_sqrts feeds MC_* ENERGY tag
do_rivet appends `:ENERGY={rivet_sqrts}` to every `MC_*` analysis (common_run_interface.py:2982-2983); the curated MC set is always tagged with ebeam1+ebeam2.
