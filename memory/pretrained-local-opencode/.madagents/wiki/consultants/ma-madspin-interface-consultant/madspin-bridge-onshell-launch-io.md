---
description: in-slice I/O and bookkeeping wiring of none(run_bridge)/onshell(run_onshell)/pickle launch paths — input_format detection, parser selection, gen cap, cross_section/new_wgt -> interface cross/branching_ratio, ms_dir pickle param_card check
---

# none / onshell / pickle launch paths — interface I/O wiring

The dispatch into these three paths is on the madspin-launch-and-decay page (do_launch :617-624).
This page caches the **interface plumbing** inside them: input parsing, event-count-driven
generation, and the cross-section/BR bookkeeping that MadGraph consumes. The decay matrix-element
generation itself (decay.py / generate_events internals) is out of slice.

## input_format auto-detection (run_bridge :855-870)
`spinmode='none'` / `'onshell'` resolve `input_format=='auto'` from the **filename** at launch:
- `'.lhe' in filename` -> `'lhe'`; `'.hepmc' in filename` -> `'hepmc'`; else `raise Exception("fail to recognized input format automatically")` (:855-861).
- `'lhe'`/`'lhe_no_banner'` -> `lhe_parser.EventFile`; `lhe_no_banner` sets `allow_empty_event=True` (:863-866).
- `'hepmc'` -> `madgraph.various.hepmc_parser.HEPMC_EventFile`, `allow_empty_event=True`, logs "Parsing input event to know how many decay to generate. This can takes few minuts." (:868-872).
- Note this is a *second* input_format resolution distinct from the do_import-side `.lhe` tail check (:217-218) used by the pure-decay shortcut (see madspin-import-resolution).

## counting which/how-many to decay (run_bridge :876-891, run_onshell :1411-1421)
- `asked_to_decay` = set of PDGs from `list_branches` keys, expanding multiparticle defs via `mg5cmd._multiparticles`, else `name2pdg` (:830-835 / :1389-1395).
- Iterate events; for each `status==1` particle with `pdg in asked_to_decay`, increment `to_decay[pdg]` (:882-885).
- **hepmc shortcut**: stop after a fixed sampled-event count, then extrapolate counts by `<factor> * filesize/currpos` (factor >1 to avoid coincidence with nevents) (:885-891 — read the count and factor fresh). So hepmc decay counts are *estimated*, not exact.
- run_onshell with `fixed_order` sets `orig_lhe.eventgroup=True` and unwraps `event=event[0]` (NLO counter-events) (:1410-1416).

## generation event-count cap (run_bridge :918-953)
Per-PDG generation calls `self.generate_events(pdg, min(nb_needed_or_nb_event, CAP), mg5, ...)`.
The decay-sample size is **hard-capped** regardless of input nevents (CAP hardcoded at :918-953 — read fresh). Branches:
- `nb_needed == nb_event` (one per event): `generate_events(pdg, min(nb_needed, CAP))` (:918-920).
- `nb_needed % nb_event == 0` (integer multiple): if `len(list_branches[name])==nb_mult` generate `nb_event`; else `cumul=True` (:921-930).
- else if `cross_section` set (hard-coded): `cumul=True`, swallowing `ZeroResult` -> "Branching ratio is zero for this particle. Not decaying it" and drop the pdg (:931-941).
- else (inconsistent particle counts, no forced xsec): per single/multi branch fall-through (:944-953). The commented-out InvalidCmd at :949 records the historical "bridge mode does not support event files where events do not all share the same final state" limitation — workaround is forcing the cross-section. NOTE: the *active* (not commented) version of this same InvalidCmd still fires later in the BR-computation block (:996, :998) when multi-particle BRs are inconsistent — so the limitation is only partially relaxed.

## BR computation against banner widths (run_bridge :957-1005)
When `cross_section` NOT set, compute branching ratio from generated decay cross-sections vs banner total widths:
- `totwidth = float(banner.get('param','decay',abs(pdg)).value)` (:963).
- one-per-event: `pwidth = sum(event_files[k].cross)`; `br *= pwidth/totwidth`; if `pwidth` exceeds `totwidth` by more than a small tolerance -> `logger.critical("Branching ratio larger than one for %s")` (:964-970 — the tolerance is the BR>1 guard, read the factor fresh).

## cross_section / new_wgt -> interface-exposed values (:1006-1024)
This is the seam MadGraph consumes (`cross`, `branching_ratio`, `error` read off the interface, see madspin-launch-and-decay :680-687):
- non-lhe input zeroes `self.cross,self.error` (:1006-1007); then `self.cross *= br`, `self.error *= br` (:1008-1009).
- `cross_section` NOT set -> `banner.scale_init_cross(self.branching_ratio)` (:1012-1013).
- `cross_section` set:
  - `lhe_no_banner`/`hepmc` with no init -> `cross = sum(cross_section.values())`, `error=0`, `branching_ratio=1` (:1016-1020).
  - else -> `banner.modify_init_cross(cross_section)`; `branching_ratio = new_cross/self.cross`; `self.cross = new_cross` (:1021-1024).
- `new_wgt` (default `'cross-section'`, allowed `BR`) decides per-event weight: `'cross-section'` -> `event.wgt *= self.branching_ratio` (global BR); `'BR'` -> local per-particle `br = decay_file.cross/tot_width` then `event.wgt *= br` (:1107-1110, :1163-1167). The per-event reassignment loop is decay-merge internal; the *option's* effect on which normalization the interface reports is in slice.

## how `set cross_section ...` populates the per-PDG dict
`cross_section` is registered as a TYPED-DICT param `add_param('cross_section', {'__type__':0.})` (interface_madspin.py:74) — same machinery as run-card `pt_min_pdg` dicts. So it is per-PDG, float-valued, and ACCUMULATES rather than replaces. The `ConfigFile.__setitem__` dict branch (banner.py:1240-1262) parses `set cross_section KEY VALUE` (also `KEY,VALUE` / `KEY:VALUE`) into `{KEY:VALUE}` and `.update()`s the existing dict (`full_reset=False`, :1260). Therefore multiple lines (`set cross_section 6 173`, `set cross_section 24 1.0`) build up `{6:173.0, 24:1.0}`, each forcing the post-MadSpin normalization for that PDG. This is what `sum(cross_section.values())` (:1017) and `modify_init_cross(cross_section)` (:1021) consume. An empty/default `{'__type__':0.}` (the `__type__` key stripped at registration, add_param :1342-1343) is falsy -> `if not cross_section` true -> BR-from-widths path.

## ms_dir pickle reuse (run_from_pickle :725-810)
Reached from do_launch when `ms_dir` set AND `madspin.pkl` exists (:624). Reuses a previously-generated
MadSpin scratch dir to skip ME regeneration. Interface-relevant invariant:
- loads `madspin.pkl`, re-wires `evtfile`/`mgcmd`/`mscmd`/`pid2width`/`pid2mass` from the new banner (:736-745).
- if `path_me != ms_dir`, rewrites all stored decay paths to the new ms_dir (:746-754) — directory is relocatable.
- **param_card compatibility check (:765-781)**: for every non-`decay` block, if the input banner's block differs from the pickle's banner block -> `raise Exception("The directory %s is specific to a mass spectrum. Your event file is not compatible ... Different param_card: %s different")`. So a cached ms_dir is bound to its mass spectrum; only `decay` (width) blocks may differ. MSSM param_cards are converted via `convert_to_mg5card` first (:758-762).
- replaces `banner['init']` and `banner['mgruncard']` from the new input (:783-788) so the output records the correct seed/run-card.
- if `seed` set, writes `seeds.dat` and removes all `ranmar_state.dat` to force the seed (:792-799).
- finally `generate_all.ending_run()`, then copies `branching_ratio`/`cross`/`error`/`efficiency`/`err_branching_ratio` onto the interface (:801-810).

## Cautions
- hepmc decay-count is a fixed-sample extrapolation (:885-891), not exact — relevant if a caller reasons about exact decay statistics from hepmc input.
- The generation cap (:918-953) means very high-statistics decay samples reuse a finite pool; consequences for variance are decay.py internals.
- A stale `ms_dir` from a different mass spectrum aborts hard at run_from_pickle (:765-781), not silently — but a *width-only* difference is allowed (decay blocks skipped), so reusing across width changes is intentional.

## Gaps
- generate_events internals (ME generation, cumul splitting math), decay-merge per-event sampling — MadSpin internals, out of slice.
