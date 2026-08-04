---
description: LO run_card cut parameters — defaults, cut= sub-system tags, hidden flags — as registered in RunCardLO.default_setup (banner.py)
---

# LO run_card cut parameters (RunCardLO.default_setup)

Source: `$MADGRAPH_INSTALL/madgraph/various/banner.py`, `RunCardLO.default_setup`
(class `RunCardLO` at :4187, `default_setup` at :4208). MG5_aMC v3.7.1.
Cut block runs :4303–:4490. Read each parameter's default FRESH at its cited banner.py
line — defaults drift across versions; the coordinate + name below IS the cached lookup,
not the number.

## Structural facts
- `add_param(name, default, cut='X', hidden=, include=, comment=, ...)`.
- `cut=` tag (`cuts_parameter[name]=cut`, set at banner.py:2870) is a sub-system
  group label used by the run-card WRITER to place the param in a card section.
  Single-letter: `j` jet, `b` b-jet, `a` photon, `l` lepton, `n` missing-Et(nu),
  `H` heavy, `d` decay. Two/repeated letters = pair/multi cuts: `jj`,`ll`,`aa`,
  `bb`,`bj`,`aj`,`jl`,`ab`,`bl`,`al`; `J` = inclusive-HT group; `'j'*4` etc = ordered.
  `cut=True` (bare) for global cuts: `dsqrt_shat`, `dsqrt_shatmax`, `xqcut`,
  and the `*_pdg` dict cuts.
- The `cut=` tag is NOT the Fortran enforcement; it is card-layout metadata only.

## Defaults — registry (read the value at the cited banner.py line)
Defaults drift; the coordinate + name is the lookup, not the number. Sentinel encoding
(version-STABLE mechanism, keep): a `*max` cut = -1 means OFF; an eta-min / mass-min = 0
means OFF; a negative eta-max disables the η cut.
- globals: :4305 `bwcutoff` ; :4306 `cut_decays` (bool, cut='d') ; :4307 `dsqrt_shat` /
  :4308 `dsqrt_shatmax` (off-sentinels) ; :4309 `nhel` (include=False, mode 0=sum) ;
  :4310 `limhel` (hidden, relative helicity keep-threshold).
- pt-min: :4312 `ptj` :4313 `ptb` :4314 `pta` :4315 `ptl` :4316 `misset` :4317 `ptheavy`
  (comment "apply on particle heavier than 10 GeV").
- pt-max (`*max`, off-sentinel): :4319 `ptjmax` :4320 `ptbmax` :4321 `ptamax` :4322 `ptlmax`
  :4323 `missetmax`.
- E cuts (hidden; min-sentinel / max-sentinel off): :4325–:4332 `ej eb ea el ejmax ebmax eamax elmax`.
- eta-max: :4334 `etaj` :4335 `etab` :4336 `etaa` :4337 `etal` (negative = η cut OFF).
  eta-min (0=off): :4339 `etajmin` :4340 `etabmin` :4341 `etaamin` :4342 `etalmin`.
  NOTE: `etajmin` registered with cut='a' (likely cosmetic typo; cut= is layout-only).
- DR-min: :4344 `drjj` ; :4346 `drll` ; :4347 `draa` ; :4349 `draj` ; :4350 `drjl` ; :4353 `dral`
  (active DR defaults); `drbb drbj drab drbl` off by default. DR-max :4354–:4363 off-sentinel.
- inv-mass-min (0=off): :4365 `mmjj` :4366 `mmbb` :4367 `mmaa` :4368 `mmll`
  ; :4373 `mmnl` (cut='LL', neutrino+lepton system). max off-sentinel.
- :4376 `ptllmin` / :4377 `ptllmax` (pt of lepton-pair sum).
- :4378–:4381 `xptj xptb xpta xptl` (min pt of at-least-one of that type).
- ordered jet pt :4383–:4390 `ptj1min..ptj4min` / max ; :4391 `cutuse`.
- ordered lepton pt :4393–:4400 `ptl1min..ptl4min` / max.
- HT :4402 `htjmin` / :4403 `htjmax` (sum of light-jet pt) ; :4404 `ihtmin` / :4405 `ihtmax`
  (inclusive HT incl heavy jets) ; :4406–:4411 `ht2min ht3min ht4min` + maxes.
- photon isolation (Frixione) :4413 `ptgmin` (cut='aj') ; :4414 `r0gamma` (hidden)
  ; :4415 `xn` (hidden) ; :4416 `epsgamma` (hidden) ; :4417 `isoem` (bool, hidden).
- :4418 `xetamin` / :4419 `deltaeta` (VBF rapidity-gap style).
- merging-shape :4420 `ktdurham` ; :4421 `dparameter` ; :4422 `ptlund`.
- :4423 `pdgs_for_merging_cut` (hidden; default PDG set) ; :4424 `maxjetflavor`
  ; :4425 `xqcut` (cut=True).
- PDG-specific dict cuts (include=False) :4473–:4479 `pt_min_pdg pt_max_pdg E_min_pdg
  E_max_pdg eta_min_pdg eta_max_pdg mxx_min_pdg` ; :4480 `mxx_only_part_antipart`.
  Lowered into system arrays `pdg_cut/ptmin4pdg/...` by update_system_parameter_for_include
  (:4701). Cap on distinct PDGs enforced at :4714 (read the cap there); negative PDG forbidden
  (cuts are symmetric, :4717); cannot target light q/b/lepton/gluon/photon — physics codes
  1-5,21,22,11,13,15 rejected (:4722).

## LO vs NLO parameter-name / default divergence (do not conflate)
The NLO run_card (`RunCardNLO.default_setup`, banner.py:5611+) uses DIFFERENT param names
AND different defaults for the same physics. Read each class's own line; never carry an LO
number to NLO. The load-bearing distinctions are NAME + convention, not magnitude:
- **Pair inv-mass NAME differs**: LO uses `mmll` (banner.py:4368, `cut='ll'`) — same-flavour
  OS l+l- pairs only (setcuts.f:399 comment `!only on l+l- pairs (same flavour)`;
  s_min = mmll*|mmll|). NLO uses `mll` (banner.py:5724, all OS pairs) AND `mll_sf`
  (banner.py:5725, same-flavour OS only). Read each default at its own line.
- **Setting `mll` in an LO run_card is rejected**: `mll` is not an LO key, so `set run_card mll X`
  falls through to `common_run_interface.py:6359` → `logger.warning('invalid set command ...')`
  then `:6366-6368` suggests close matches ("Did you mean one of the following run_card options:")
  — `mmll`, `mmllmax` both contain the substring "mll" so they ARE suggested. Cut is discarded.
- **Default-CONVENTION divergence** (a doc listing eta cuts OFF as "LO" actually has NLO values):
  LO ships POSITIVE eta defaults (η cut ON); NLO ships eta cuts OFF via the negative sentinel
  (etaj/etal < 0). The negative-sentinel SEMANTICS (η<0 disables the η cut) is real at both
  classes (LO `etab` uses it); only NLO ships the eta cuts OFF by default. Verify which class
  before adopting any cut default — read that class's banner.py line for the actual number.

## auto_ptj_mjj
:4304 `auto_ptj_mjj` True (hidden). Comment at writer banner.py:3990 "Automatic setting
of ptj and mjj if xqcut>0". Acts in BOTH check_validity (Python) and setcuts.f (Fortran)
— see runcard-cut-validity.md and cuts-f-filter.md.
