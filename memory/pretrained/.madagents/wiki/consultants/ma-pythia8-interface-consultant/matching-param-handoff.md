---
description: How setup_Pythia8RunAndCard translates run_card matching knobs (ickkw/xqcut/ktdurham/ptlund/maxjetflavor/sys_matchscale) into Pythia8 MLM and CKKW-L card parameters.
---

# Matching-parameter handoff: run_card -> PY8 card

`madevent_interface.py:4307 setup_Pythia8RunAndCard(PY8_Card, run_type, use_mg5amc_py8_interface)`. The three branches (MLM / CKKW / default) are keyed on `run_type` (set in `do_pythia8:4671-4677`). My slice owns the *parameter translation*; scheme *selection logic* is the matching slice's.

## Always (all run_types)
- `JetMatching:setMad = False` (`:4398`) — PY8 reads params from this card, not the LHE banner.

## MLM branch (`run_type=='MLM'`, i.e. run_card ickkw==1) — `:4399-4471`
- Veto-write-out `Merging:TMS / Merging:Process / Merging:nJetMax` (`:4403-4405`) so they don't leak into the MLM driver.
- `JetMatching:qCut`: if still -1.0, set to `<factor>*run_card['xqcut']`, where `<factor>` is the code literal at `madevent_interface.py:4409` (currently 1.5 — read fresh, do not cache as universal). If qCut < that same floor => logger.error advising larger qCut / smaller xqcut (`:4411-4415`).
- `Beams:setProductionScalesFromLHEF = True` (`:4419`).
- old-interface only: `SysCalc:qWeed` <- `xqcut` if -1 (`:4422-4423`); `SysCalc:qCutList` from `sys_matchscale` (auto => the code factor-list at `:4426` × qCut, filtered to > the qCut floor) (`:4425-4436`) — read the factor-list fresh at `:4426`, do not cache the literals.
- `JetMatching:doVeto=False` when old-interface AND use_syst (driver/SysCalc does the veto) (`:4452-4455`).
- `JetMatching:merge=True`, `JetMatching:scheme=1`, `JetMatching:nQmatch <- run_card['maxjetflavor']`, `JetMatching:coneRadius=1.0` (`:4456-4462`).
- `JetMatching:nJetMax`: if -1, set to `proc_characteristic['max_n_matched_jets']` (`:4467-4471`).

## CKKW branch (`run_type=='CKKW'`, i.e. ktdurham>0 OR ptlund>0) — `:4473-4565`
- Requires `Merging:Process` filled (not `'<set_by_user>'`) else InvalidCmd (`:4476-4480`). This is a hard stop — CKKW-L needs the user-declared hard process.
- Veto-write-out `JetMatching:qCut / doShowerKt / nJetMax` (`:4485-4487`).
- ktdurham>0 & ptlund<=0 => `Merging:doKTMerging=True`, `Merging:Dparameter <- run_card['dparameter']`, CKKW_cut='ktdurham' (`:4491-4495`). NB these two are set on `PY8_Card.subruns[0]` (`:4492-4494`), not the top-level card.
- ptlund>0 & ktdurham<=0 => `Merging:doPTLundMerging=True` (also on `subruns[0]`, `:4497`), CKKW_cut='ptlund' (`:4496-4498`).
- BOTH on => InvalidCmd "*both* cuts cannot be turned on" (`:4499-4503`).
- `Merging:TMS` <- run_card[CKKW_cut] if -1 (`:4512-4514`); error if TMS < CKKW_cut (`:4518-4522`).
- `SysCalc:qWeed` <- CKKW_cut value if -1 (`:4507-4508`).
- `TimeShower:pTmaxMatch=1`, `SpaceShower:pTmaxMatch=1`, `SpaceShower:rapidityOrder=False` (`:4524-4526`).
- old-interface+use_syst => `Merging:applyVeto=False`, `Merging:includeWeightInXsection=False` (`:4528-4532`).
- `Merging:nQuarksMerge <- run_card['maxjetflavor']` (`:4535`); `Merging:nJetMax` <- max_n_matched_jets if -1 (`:4539-4542`).
- `SysCalc:tmsList` from `sys_matchscale` (auto => the same code factor-list × TMS, filtered `>CKKW_cut`) (`:4543-4554`) — read the factors fresh at `:4543-4554`.

## default branch (no merging) — `:4566-4575`
Veto-write-out all of `Merging:TMS/Process/nJetMax` and `JetMatching:qCut/doShowerKt/nJetMax` so stray merging settings don't trigger vetoes in an unmerged run.

## run_card matching knobs (banner.py)
- LO `ickkw`: `banner.py:4284` add_param, hidden, `allowed=[0,1]` (0=fixed-order, 1=MLM) — read default at `:4284`. xqcut>0 with ickkw==0 => logger.error "Potentially not fully consistent" + sleep (`:4562-4565`). maxjetflavor==6 with ickkw>0 => InvalidRunCard (`:4556-4557`).
- NLO `ickkw`: `banner.py:5712`, `allowed=[-1,0,3,4]` (0=none, 3=FxFx, 4=UNLOPS [no MG5aMC interface], -1=NNLL+NLO jet-veto) — read default at `:5712`.
- `pdgs_for_merging_cut`: `banner.py:4423` (read default list at `:4423`), reset to `proc_characteristic['colored_pdgs']` at `:4782`.
- `sys_matchscale`: `banner.py:4432` default `'auto'`, `include=False`, hidden. Consumed by the qCutList/tmsList logic above.

## MadGraphSet raise asymmetry — WHICH params FATAL if the user co-sets (banner.py:2096-2107)
`MadGraphSet` raises `Exception("The parameter %s is already set...")` iff param present AND in `user_set` AND `force` not passed (`:2103-2107`). Two classes in setup_Pythia8RunAndCard:
- **Sentinel-guarded, force=True** — `JetMatching:qCut/nJetMax` (MLM), `Merging:TMS/nJetMax` (CKKW): only set when the card value is still the `-1`/`-1.0` sentinel (`:4408,4468,4512,4539`), so a user value (non-sentinel) is *respected* (MG never calls MadGraphSet → no raise).
- **Unconditional, NO force** — MLM `JetMatching:merge/scheme/nQmatch/coneRadius` (`:4456-4462`), `JetMatching:setMad` (`:4398`); CKKW `TimeShower:pTmaxMatch`/`SpaceShower:pTmaxMatch`/`SpaceShower:rapidityOrder` (`:4524-4526`), `Merging:nQuarksMerge` (`:4535`): a user who *also* sets any of these in pythia8_card.dat triggers the FATAL "already set" raise. This is the real mechanism behind the "parameter already set" error a user hits — it is these unconditional non-forced sets, not the auto-managed sentinel ones. (`Merging:doKTMerging/doPTLundMerging/Dparameter` are set on `subruns[0]` `:4492-4497`, same no-force → same raise on a co-set subrun value.)

## Doc-myth corrections / scope boundaries
- **FxFx pythia8_card params (`JetMatching:doFxFx`, `qCutME`) are NOT written by this LO path.** Whole-tree grep: absent from madevent_interface.py, banner.py PY8Card default_setup, and `pythia8_card_default.dat`. FxFx = `ickkw=3` (NLO). NLO+PS FxFx is driven in `amcatnlo_run_interface.py` by *patching the Pythia8 plugin header* `MCatNLO/Scripts/JetMatching.h` against `$pythia8_path/include/Pythia8Plugins/JetMatching.h` (`:4020-4021`) — a compiled-plugin mechanism, not a card-param mechanism. Boundary: amcatnlo slice + Pythia-plugin-internal.
- **`Merging:doMGMerging` is not an MG-managed param** — not registered in PY8Card `default_setup` (only `doKTMerging` `banner.py:1989`, `doPTLundMerging` `:1991`). If a user writes it, it is not one of MG's known/auto-set knobs.
- **`JetMatching:merge` for CKKW is not written "off"** — MG only sets it (True) in the MLM branch (`:4456`); in CKKW it is left at registered default `False` (`banner.py:1955`, `always_write_to_card=False`) so it is simply not emitted. Effectively off, never an explicit `=off`.
- **`JetMatching:setMad=False` (`:4398`, all run_types)** deliberately makes PY8 read matching params from the *card*, not the LHE banner. So although the run_card IS serialized into the LHE `<MGRunCard>` block (`banner.py:465`), the MG5aMC driver does not consume ickkw/xqcut/maxjetflavor from that header — those reach PY8 as explicit card params. Pythia8's own `JetMatchingMadgraph` header-reading (active only under setMad=on) is EXTERNAL to MG source.

## DJR / Main:InternalAnalysis (banner.py:2366-2374)
- On the default `not use_mg5amc_py8_interface AND direct_pythia_input` (main164) path, when translating `HepMC:output`→`Main:HepMC=on`, the card writer additionally emits `InternalAnalysis:output = ./djrs.dat` **iff the user set `Main:InternalAnalysis = on`** (`:2372-2374`). So `Main:InternalAnalysis` is a user-set enabler, not an MG default.
- The `djrs.dat` histogram file is produced by main164 (external); MG then reads it (`extract_cross_sections_from_DJR`, madevent_interface.py:5019), and **outputs it as HwU** (`:5042 format='HwU'` → `<tag>_djrs.dat` `:5044`). The MG-side DJR product is HwU, not XML — the "XML not HwU" doc phrasing is about PY8's internal histogram, external to MG.

## CAUTION
- Several `SysCalc:*` and veto-disabling steps fire **only when `use_mg5amc_py8_interface` (old interface) AND `run_card['use_syst']`**. On the default `main164` path these are skipped — the systematics/qCutList machinery is an old-interface feature. This is one facet of the broader interface divergence (name translation + SysCalc disabling on write) — see interface-divergence-main164-vs-old.md.
- `JetMatching:qCut` auto = the factor×xqcut (`:4409`), NOT `xqcut` (the factor is >1). A user who sets xqcut and expects qCut==xqcut is wrong.
