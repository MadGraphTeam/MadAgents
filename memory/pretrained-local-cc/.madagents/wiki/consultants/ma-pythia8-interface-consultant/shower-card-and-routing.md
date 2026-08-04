---
description: ShowerCard (NLO shower_card.py) supported showers + qcut/njmax mapping, and do_shower routing (LO madevent vs NLO amcatnlo), legacy do_pythia/Pythia6.
---

# ShowerCard + do_shower routing

## `shower_card.py:40 class ShowerCard(banner.RunCard)` (NLO+PS shower steering)
- Supported showers via `names_dict` per-shower keys: **PYTHIA8, PYTHIA6, HERWIG6, HERWIGPP** (`add_param` py8=/py6=/hw6=/hwpp= and `all_sh` with sh_postfix `_py8/_py/_hw/_hwpp`, `:77-110`).
- `__new__` (`:64`) bypasses RunCard's LO/NLO factory — always a ShowerCard.
- Merging knobs (`:178-182`): `Qcut` (`-1.0` sentinel default, read at `:178-182`) -> py8 name **`qcut`** (maps to Pythia8 `JetMatching:qCut` driver input); `njmax` (`-1` sentinel) -> py8 `njmax`. These are the FxFx-side merging-scale handles on the shower card.
- PY8-specific flags (`:195-216`): `qed_shower` (T), `primordialkt` (F), `space_shower_me_corrections` (F, ISR MECs), `time_shower_me_corrections` (T, FSR MECs), `time_shower_me_extended` (F), `time_shower_me_after_first` (F), and `pythia8_options` dict -> py8 `extra_line` (arbitrary extra PY8 params). The shower physics these toggle is out-of-slice; the card plumbing is in-slice.
  - **ASYMMETRIC ME-correction defaults** are real and deliberate: `space_shower_me_corrections=False` (ISR MECs OFF, `:202-203`) vs `time_shower_me_corrections=True` (FSR MECs ON, `:204-205`). This is a shower_card (NLO+PS/MC@NLO shower steering) feature ONLY — the LO `PY8Card` emits no MEcorrections param. NOTE: the `py8=` keys are the MG5aMC_PY8_interface driver's own names (`space_shower_me_corrections` etc.), written UPPERCASED by names_dict translation — NOT the native Pythia8 settings `SpaceShower:MEcorrections`/`TimeShower:MEcorrections`. Whether Pythia8-standalone's native default for these differs is a Pythia-internal fact (out of slice).
- UE/hadronisation/stable/PDF knobs (`:134-176`): `ue_enabled` (F), `hadronize` (T), `lambda_5` (ignored by PY8), `*_stable` flags, `b_mass`, `pdfcode` (1=same as NLO).
- `tune_ee`/`tune_pp` add_params are **commented out** (`:211-214`) — not active; tune set elsewhere. TRAP: `tune_ee`/`tune_pp` ARE still listed in `int_vars` (`:53`) but their `add_param` calls are commented, so they're never registered in `names_dict` and never written — the int_vars membership is dead. Don't infer "tune is a shower-card knob" from the int_vars list.

## string_vars write path (differs from typed-vars translation)
`string_vars = ['extralibs','extrapaths','includepaths','analyse']` + `dm_1..dm_99` (`:50-52`). The `write_card` string branch (`:354-380`) does NOT route through the `names_dict` translation the typed branch uses (`:396`):
- `EXTRALIBS` (default `"stdhep Fmcfio"`), `EXTRAPATHS` (`"../lib"`), `INCLUDEPATHS` (`""`) have NO `names_dict` per-shower entry — they're written via the fallback `key.upper()=value` line (`:378`) with their own uppercase name, **identical for every shower**. These are the link-time library/path knobs for the MC@NLO analysis `.o`.
- `ANALYSE` (`:192-193`, py8=`py8uti`/py6=`pyuti`/hw6=`hwuti`/hwpp=`hwpputi`) IS names_dict-translated (`:356-369`). When empty it falls back to `stdhep_dict[self.shower]` (`:358-362`) — but `stdhep_dict` only has `HERWIG6`/`PYTHIA6` keys (`:62`); for PYTHIA8/HERWIGPP the KeyError is swallowed (`pass`, `:361-362`) so `value` stays empty and it writes `PY8UTI=""`. So the default-analysis-object fallback is a PY6/HW6-only feature; PY8 with empty analyse writes an empty `PY8UTI`.

## Parallelization + decay-mode plumbing
- `nsplit_jobs` (`:122`, default read at `:122`) — N parallel shower jobs (comment "< 100!!"); `combine_td` (default True, `:123`) combines the per-job topdrawer/HwU files when nsplit_jobs>1. These are the shower-card-level parallelization handles (distinct from PY8's run_mode split in do_pythia8).
- `DM_1..DM_99` (`:185-186`, hidden) — per-multiplicity decay syntax strings ("warning syntax depend of the PS used"). `read_card` (`:239-244`) special-cases these: any `DM_*` key read is recorded, and every `dm_<i>` not present in the file is reset to `''`. `write_card` skips empty `dm_*` (`:371-372`). So unset decay slots never reach the written card.
- `is_4lep` (py6 only, `:172-173`) and `is_bbar` (hw6 only, `:174-175`) — shower-specific special-process flags with no PY8 entry; silently dropped for PY8 by the `names_dict` KeyError-pass at `:398-399`.
- `write_card` (`:332`): translates internal keys to per-shower fortran names via `names_dict[key][SHOWER]` (UPPERCASED), producing the `KEY=value` lines the MC@NLO shower driver reads. Type formatting (`:342-394`): bool -> `.true.`/`.false.` except PYTHIA6 `ue_enabled`/`hadronize` -> numeric `1`/`0`; int -> `%d`; float -> **`%4.3f`** (so `qcut` -> `QCUT=15.000`); str -> quoted, with `analyse` falling back to `stdhep_dict[shower]` (`mcatnlo_pyan_stdhep.o` etc.) when empty. `pythia8_options` dict -> a quoted multi-line `k = v` block under fortran name `EXTRA_LINE`, but **only for PYTHIA8** (empty string for other showers, `:385-392`). Keys whose `names_dict` entry lacks the current shower are silently dropped (`:398-399`).

## LO `do_shower` (`madevent_interface.py:4203`)
- `_interfaced_showers = ['pythia','pythia8']` (`:2044`).
- With no explicit shower and not --no_default: picks one by `shower_priority = ['pythia8','pythia']` => **pythia8 preferred** (`:4218-4220`).
- --no_default => runs all interfaced showers (each self-checks card existence).
- Dispatches to `do_pythia8` / `do_pythia` via exec_cmd.

## NLO `do_shower` (`amcatnlo_run_interface.py:1529`)
- Routes through `run_mcatnlo(evt_file, options)` after `ask_run_configuration('onlyshower')`. The MC@NLO matching internals inside run_mcatnlo are **out-of-slice** (Pythia/MC@NLO algorithm). The shower_card is the interface artifact this slice owns; the LHE input here is `events.lhe` (not .gz).

## Legacy Pythia6 `do_pythia` (`madevent_interface.py:5320`)
- Pythia6 path; card `Template/LO/Cards/pythia_card_default.dat` sets MSTP(61/71) (showering), MSTJ(1) (hadronization), MSTP(81) (MPI), MSTU(21) (error tolerance), LHAID (PDF id) — read the values in the template. Legacy / pythia-pgs path.
