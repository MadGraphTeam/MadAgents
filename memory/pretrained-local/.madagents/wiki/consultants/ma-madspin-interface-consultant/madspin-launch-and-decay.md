---
description: do_decay grammar warnings and do_launch spinmode dispatch / seed / BW_cut hard-threshold abort / decayed-file output (interface_madspin.py)
---

# do_decay and do_launch

## do_decay (`:420`)
Appends a decay branch to `self.list_branches[init_part]`. Three source-visible warnings:
- polarization `{...}` syntax with `spinmode=='none'` (:427-428): rest-frame interpretation "likely not what you expect".
- polarization `{...}` with `spinmode=='onshell'` (:429-430): "not validated … sub-optimal method which can likely lead to bias".
- `'='` (coupling-order restriction) in branch with `spinmode in [full,madspin]` (:431-432): "coupling order restriction are not associated to specific Branching Ratio. The total cross-section might therefore use the wrong branching ratio."
Branch is reordered via `self.decay.reorder_branch` (:433).

### Spin-correlation per spinmode (interface-visible)
`help_set` (:528) states verbatim: "set spinmode=none: mode with simple file merging. **No spin correlation attempt.**" This is the one interface-level source statement of per-mode correlation semantics. Reading the interface-visible signals together:
- `madspin` (default, :69) / `full` -> full spin-correlated path (fall-through at :634); correlations preserved. Precise algorithm is decay.py internals.
- `none` -> `run_bridge` (:617-618); NO spin correlation (:528). Polarization tags reinterpreted in the decaying-particle rest frame (:427-428 warning) "likely not what you expect".
- `onshell` -> `run_onshell` (:619-620); on-shell |M|²-via-f2py reweight (does use MEs) but polarization "not validated … sub-optimal method which can likely lead to bias" (:429-430).
So the mode that silently drops correlations is **`none`**; the default `madspin` preserves them.

## Constructor (`__init__ :142`)
`MadSpinInterface(event_path=None)` (:142). `@misc.mute_logger()` decorated. Inits
`self.options = MadSpinOptions()` (:157), `self.list_branches={}`, `self.to_decay={}`,
`self.mg5cmd = master_interface.MasterCmd()` (:163), `self.seed=None` (:164),
`self.me_run_name=""` (:166, "Events directory name ... used by madevent, not used internally").
If `event_path` given -> `self.do_import(event_path)` immediately (:169-171). So constructing the
interface with a path triggers the full banner-handoff/sentinel resolution at construction time
(this is how do_decay_events :4203 drives it: `MadSpinInterface(args[0])`).

## do_launch (`:607`)
`me_run_name` is set FIRST (before the spinmode dispatch): `parse_launch` parses `-n NAME`
(parser at the `parser_launch` def, `-n/--name` "When NOT run in standalone instruct MG5aMC where
to store the events file"); `options.name` -> `self.me_run_name` else `''` (:611-615). This runs for
ALL spinmodes (none/onshell/full), not just the full path. `me_run_name` is then read by the
MG-side do_decay_events to choose the output run dir (see madspin-mg-invocation :4217-4229).

Dispatch by spinmode (after the `-n` parse):
- `spinmode in ['none']` -> `run_bridge(line)` (:617-618). Simple file-merge decay; supports 3+ body decays; reads input via lhe/hepmc parser (run_bridge :818).
- `spinmode == 'onshell'` -> `run_onshell(line)` (:619-620, def :1373).
- `spinmode == 'bridge'` -> hard Exception "Bridge mode not available" (:621-622). (Note: 'bridge' is NOT in the allowed list, so this is unreachable via normal set.)
- otherwise (full / madspin) -> falls through to the full spin-correlated path below.

Full/madspin path:
- `ms_dir` + `madspin.pkl` present -> `run_from_pickle()` and return (:624).
- `check_launch` (:565): needs branches (unless `onlyhelicity`), needs an events_file, and requires LHEF v3 when `ickkw>0` (matching/merging) (:574-576).
- branch/final-state cross-check loop (:630-651): if no requested decay particle is in the production final state, logs "Nothing to decay …" and returns (unless onlyhelicity).
- **BW_cut above the hard NWA threshold -> hard Exception** ("much too large … for narrow width approximation", :653-654 — read the threshold fresh). This is the only BW_cut abort; the import-time NWA-threshold case (:253) is a non-fatal critical.
- seed: if `seed==0` (sentinel), pick a random seed within the seed-space bound, log it, record in history (:658-662). A seed above that bound -> Exception (:664-666 — read the bound fresh).
- history is serialized into a `madspin` banner block (:669-670) so the decayed file records the exact MadSpin commands.
- core: `madspin.decay_all_events(self, banner, events_file, options).run()` (:674-678) — decay generation itself is MadSpin internals, out of slice.

## do_define (`:531`) — multiparticle bookkeeping (two-tier)
`define NAME = ...` in the card delegates to `self.mg5cmd.exec_cmd('define %s' % line)` (:535), then
snapshots ALL of mg5cmd's multiparticles into `self.multiparticles_ms` (:543-544). On exec failure
it deletes the just-added key from `multiparticles_ms` if present and re-raises (:537-542). So there
are TWO multiparticle registries: `mg5cmd._multiparticles` (authoritative, used by the branch/final-
state cross-check at :630-645 and `asked_to_decay` expansion at :831-836) and the MS-local
`multiparticles_ms` snapshot. `complete_decay` tab-completion routes to `mg5cmd.complete_generate`
(:558-563); `complete_define` to `mg5cmd.complete_define` (:551-556). These are how a card's
`define sq = ur ur~` then `decay go > sq j` resolves the multiparticle decay target.

## Output (:689-723)
- input re-gzipped; decayed output gzipped to `<events_file>` with `.lhe`->`_decayed.lhe` (:695-697) i.e. `decayed_events.lhe` -> `<run>_decayed.lhe.gz`.
- `madspin_card.dat` archived next to the run as `madspin_card_for_<evt>.dat` (RunMaterial-aware) (:702-723).
- exposes `branching_ratio`, `cross`, `error`, `efficiency`, `err_branching_ratio` on the interface (:680-687) — consumed by the MadGraph caller.

## Cautions
- `-n NAME` only matters when driven by MG5aMC (standalone ignores placement); see madspin-mg-invocation page.
- spinmode='bridge' string reaches an Exception but cannot be set through `check_set` (allowed list excludes it).

## Gaps
- run_bridge / run_onshell internal algorithms beyond the launch entry are largely MadSpin internals; the dispatch + I/O wiring here is in slice.
