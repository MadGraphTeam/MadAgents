---
description: EW Sudakov reweighting in ReweightInterface — include_sudakov flag, LO[only=QCD] --ewsudakov generation, do_reweight width-to-zero/ntadpole gating, five SUD ratios (sudrat0..4), damping when the ratio exceeds a threshold, double-reweight guard, weight-id '2'+tag convention.
---

# EW Sudakov reweighting

A distinct branch of `ReweightInterface` (`$MADGRAPH_INSTALL/madgraph/interface/reweight_interface.py`, v3.7.1) that applies the EW Sudakov logarithm approximation as an event reweight, separate from both Systematics (scale/PDF) and ordinary matrix-element reweighting. Activated by `change include_sudakov True` in `reweight_card.dat`.

## Activation (`do_change`, ri.py:445-448)
```
elif args[0] == 'include_sudakov':
    if args[1] == 'True':
        self.inc_sudakov = True
        self.rwgt_mode = 'LO'
```
Default `self.inc_sudakov = False` (ri.py:119). Setting it True also **forces `rwgt_mode='LO'`** — Sudakov is computed via a LOonly QCD generation, not full NLO ME reweighting.

## Process generation (`get_LO_definition_from_NLO`, ri.py:223-290)
With `ewsudakov=True` the generated reweight process command is rewritten (ri.py:276):
```
commandline = commandline.replace("--no_warning=duplicate", "[LOonly=QCD] --ewsudakov")
```
So the reweight ME is generated as `add process ... [LOonly=QCD] --ewsudakov`. The Sudakov output format differs: `output ewsudakovsa <path> --prefix=int` (ri.py:1805) instead of the usual standalone output.

## do_reweight gating — widths to zero, ntadpole=1 (common_run_interface.py:1022-1033)
Triggered by `self.proc_characteristics['ew_sudakov']` (set on the generated reweight dir, not the original event file):
- **All particle widths forced to zero** unless `complex_mass_scheme` — `no_width = [p for p in ufomodel.all_particles if p.width != zero]`, with `logger.info('Setting all particle widths to zero (needed for EW Sudakov approximation).')`.
- **`param_card['tadpole'].get(1).value = 1.`** (ntadpole=1). If the model has no `tadpole` block → `logger.warning('The model has no 'ntadpole' parameter. The Sudakov approximation for EW corrections may give wrong results.')` — proceeds anyway with possibly wrong results.

## Module + compilation (`launch_actual_reweighting`, ri.py:555-566, 2143-2160)
- Imports `<rwgt_dir>.bin.internal.ewsud_pydispatcher` as `sud_mod` (tries `rw_me`, `rw_me_<n>`, `rw_mevirt`, `rw_mevirt_<n>`); `logger.info('EW Sudakov reweight module imported')`.
- Splits banner into `rw_me/Cards`, compiles `rw_me/Source` after setting `ewsudsa=True` in `make_opts` via `update_make_opts_full`, then compiles P* dirs.
- `get_weight_names`-style path setup returns early for Sudakov (ri.py:2234) — no per-tag liball loading; the dispatcher handles it.

## Weight computation — five SUD ratios (`calculate_weight`, ri.py:1300-1362)
Per event: builds momentum array `p_in` in MG pdg order (validated against `sud_mod.original_pdg_list_dict[sorted_tag]`; mismatch → `logger.critical('ERROR: order in particle momenta does not match MG convention!'); sys.exit(3)`), `gstr = sqrt(4*pi*event.aqcd)`, then `res = sud_mod.ewsudakov(sorted_tag, p_in, gstr)`. The `res` array has 6 entries (`res[0]` is the reference denominator); **five** ratios are formed as `1. + res[k]/res[0]` for k=1..5 (ri.py:1331-1336):
- `sudrat0 = 1.+res[1]/res[0]` = SUD0 (s_to_rij ON, rij_ge_mw ON)
- `sudrat1 = 1.+res[2]/res[0]` = SUD1 / **SDK_weak** (s_to_rij ON, rij_ge_mw ON) ← **the one actually applied**
- `sudrat2 = 1.+res[3]/res[0]` = SDK_weak (s_to_rij OFF, rij_ge_mw ON)
- `sudrat3 = 1.+res[4]/res[0]` = SDK_weak (s_to_rij OFF, rij_ge_mw OFF)
- `sudrat4 = 1.+res[5]/res[0]` = SDK_weak (s_to_rij ON, rij_ge_mw OFF)

Each pre-existing scale weight `el` is multiplied by `sudrat1` (ri.py:1356-1360):
```
for el in rwgt_dict:
    tag = '20' + el[-2:]
    rwgt_dict_new[tag] = rwgt_dict[el]*sudrat1  # use SDK_weak!
```

## Damping (ri.py:1338-1347)
If `abs(sudrat1)` exceeds the damping threshold (read at ri.py:1338-1347): `logger.info('ERROR: event will not be reweighted because Sudakov ratio is too large: ...')`, all six ratios reset to `1.`, `large_sud_error=True`. The event keeps its nominal weight (effectively skipped). Tally reported at end: `logger.info('Number of events thrown away due to large Sudakov: <count_errors>')` (ri.py:667-668).

## Double-reweight guard (ri.py:631-632, 966-974)
- If a Sudakov tag already exists in `event.reweight_order` → `logger.critical('This is a reweighted event file! Do not reweight with ewsudakov twice'); return`.
- Header-emission side: `int(rwgttype[-1])` IndexError → same critical message + `sys.exit(1)`.

## Weight-id convention (interacts with lhe-weight-indexing page)
- `type_rwgt` built from existing scale weight ids: each header id `<weight id='X'>` → `'2' + tag_strip` where `tag_strip = tag[1:]` (ri.py:532-535). So a scale weight `1001` produces Sudakov weight `2001`.
- Per-event: existing weight id ending `NN` → new id `'20'+NN` (ri.py:1357).
- Header body (ri.py:967-971): `<weight id='<2..>'><diff>scale_10NN_sud</weight>` where `sud_order='10'+rwgttype[-2:]`.
- If `type_rwgt==[]` (no pre-existing scale weights) → defaults to `['2001']` (ri.py:563-564).

## Cautions
- Setting `include_sudakov True` silently downgrades `rwgt_mode` to `'LO'` — you do NOT get NLO-accurate ME reweighting alongside; it is a Sudakov-log overlay on existing weights.
- Sudakov reweight **multiplies pre-existing scale weights** by SDK_weak (sudrat1) — it presupposes the event file already carries scale-variation weights (those `1NNN` ids). Without them, falls back to a single `2001`.
- Missing `ntadpole`/`tadpole` block → only a warning; result may be wrong, not an error.
- Events with `|sudrat1|` above the damping threshold are silently kept at nominal weight (counted but not reweighted).
- Re-running ewsudakov on an already-Sudakov-reweighted file → critical error / sys.exit, by design.
- RUNTIME claims here (warning text, sys.exit codes, "thrown away" tally) are read from source, not probe-confirmed — a probe of an actual NLO EW process reweight would confirm the emitted weightgroup and messages.
