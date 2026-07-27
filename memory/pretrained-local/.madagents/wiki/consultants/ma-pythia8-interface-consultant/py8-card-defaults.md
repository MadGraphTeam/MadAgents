---
description: The Pythia8 card — pythia8_card_default.dat template contents and the PY8Card class defaults/setter semantics in banner.py.
---

# Pythia8 card: template + PY8Card class

## Template `Template/LO/Cards/pythia8_card_default.dat`
Read the card for current default values — do NOT recall PY8-card defaults. Visible (uncommented) entries + coordinates:
- `Main:numberOfEvents` (`:10`) — sentinel default => all events; overridden by nevents in code (see do-pythia8-handoff).
- `HEPMCoutput:file` (`:32`). Accepted values documented `:13-29`: hepmc / hepmc.gz / hepmcremove / hepmc@<path> / /dev/null / fifo / fifo@<path>.
- MLM block: `JetMatching:qCut` (`:43`, `-1.0` sentinel → auto-derived), `JetMatching:doShowerKt` (`:46`), `JetMatching:nJetMax` (`:49`, `-1` sentinel).
- CKKW-L block: `Merging:TMS` (`:61`, `-1.0` sentinel), `Merging:Process` (`:70`, `<set_by_user>` sentinel), `Merging:nJetMax` (`:73`).
- `SysCalc:fullCutVariation` (`:78`).
- `!partonlevel:mpi` (`:87`) — commented (so MG writes no MPI toggle; Pythia's own compiled default governs). (What that default is, and MPI behaviour itself, are Pythia-internal / out-of-slice; this is just the card line.)
- `Merging:Process` note (`:64-69`): from PY8 v8.223 the value `'guess'` is allowed.

## PY8Card class `banner.py:1877 class PY8Card(ConfigFile)`
- `default_setup` (`:1898`) defines all known PY8 params. Visible params (`:1903-1921`) mirror the template. `JetMatching:*` and `Merging:*` carry `always_write_to_card=False`.
- Hidden, **always written** (`:1925-1936`): `Beams:frameType=4` (LHEF protocol constant), `HEPMCoutput:scaling` (pb normalization; the default is the mb→pb factor — read it fresh at its `:line`), `Check:epTolErr`, `JetMatching:etaJetMax` — read all default values at `:1925-1936`, do not cache the literals.
- Hidden, written only if user_set/system_set (`:1938-2008`): PDF:pSet, alphaSvalue (tune-dependent), `hadronlevel:all`, `partonlevel:mpi`, `Beams:setProductionScalesFromLHEF` (auto-True for MLM), the MLM internals (`JetMatching:merge/scheme/setMad/coneRadius/nQmatch`, `SysCalc:qCutList/qWeed/tmsList`), the CKKW internals (`TimeShower:pTmaxMatch`, `SpaceShower:pTmaxMatch`, `Merging:muFac/muRen/muFacInME/muRenInME`, `Merging:nQuarksMerge`, `Merging:doKTMerging/doPTLundMerging/Dparameter`), QED-shower switches, `Main:HepMC`/`HepMC:output` (main164-only). Read any default fresh at its `:line` in `banner.py` `default_setup`.
- `SysCalc:qCutList`/`SysCalc:tmsList` carry numeric default lists then are forced to the string `'auto'` (`:1957-1958`, `:1971-1972`) — read the lists at those lines.

## No Pythia8 `Tune` is set by MadGraph (myth-buster)
- The LO template `pythia8_card_default.dat` contains **NO `Tune:pp` / `Tune:ee` line** (verified: whole card dumped). MG5aMC does not emit any Pythia8 tune selector; Pythia8's own compiled-in default tune governs unless the *user* adds a `Tune:pp = N` line to the card (native passthrough).
- The tune-adjacent params MG *does* know are `PDF:pSet`, `SpaceShower:alphaSvalue`, `TimeShower:alphaSvalue` (banner.py`:1940-1945`, all hidden, `always_write_to_card=False` -> written only if user/system-set), each carrying comment "Parameter below is shower tune dependent." Read their defaults at `:1940-1945`; these are NOT a tune number.
- `tune_pp` / `tune_ee` appear ONLY as **commented-out** `add_param` lines in `shower_card.py:211-214` (NLO shower_card) and are dead even there (listed in `int_vars` but never registered in `names_dict`). So any "MG default tune is Monash/N" claim is false for both the LO card and the NLO shower card. (Whether a given tune index maps to Monash 2013 is a Pythia-internal fact, out of slice.)
- The LO `PY8Card.default_setup` registers **no** `SpaceShower:MEcorrections` / `TimeShower:MEcorrections` param at all (grep of banner.py: none). ME-correction toggles are a shower_card (NLO+PS) feature; on the LO path Pythia's own ME-correction defaults apply untouched.

## Subruns / nSubruns
- `add_default_subruns` (`:1880`): adds `LHEFInputs:nSubruns=1` (hidden ALWAYS_WRITTEN) and creates `subruns[0] = PY8SubRun(subrun_id=0)`. `PY8SubRun` at `:2546`.
- LHE input is set per-subrun: `subruns[0].systemSet('Beams:LHEF', ...)`.

## Setter semantics (`banner.py:2074-2110`) — key to "who wins"
- `userSet` (`:2074`): marks user_set; removes from system_set.
- `systemSet` (`:2085`): sets only if not user_set (unless `force=True`); marks system_set.
- `MadGraphSet` (`:2096`): sets only if absent OR (force OR not user_set) (`:2103`); raises **only when the param is already present AND user_set AND not forced** (`:2106-2107`) — NOT merely "already set". This is why a user value in `pythia8_card.dat` overrides MadGraph's auto-derivation for qCut/nJetMax/TMS etc. (and why MG's auto-derivations pass `force=True` when they intend to win regardless).
- `defaultSet` (`:2109`): unconditional, no user_set change.
- `vetoParamWriteOut` (`:2080`): adds to `params_to_never_write` — suppresses writeout even if set.
