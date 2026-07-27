---
description: NLO run_card cut block (RunCardNLO.default_setup + Template/NLO cuts.f/setcuts.f) — the NLO cut set, how it differs from LO, and the IR-safety constraints (jets clustered before cut, dressed leptons, massive-PDG-only per-particle cuts) that govern which fixed-order NLO / NLO+PS cuts are safe.
---

# NLO fiducial cuts — the cut block and IR-safety

Owns: the cut entries written into the NLO `run_card.dat`, and the fixed-order cut-application code in `Template/NLO/SubProcesses/`. The LO cut catalog and `Template/LO/.../cuts.f` belong to ma-kinematic-cuts-consultant. FKS subtraction internals belong to the fks slice; this page only cites the IR-safety *requirement* the cut code states, not the subtraction mechanism.

## Where the cuts live

- **Card defaults**: `$MADGRAPH_INSTALL/madgraph/various/banner.py`, `RunCardNLO.default_setup`, the `#cuts` block at **banner.py:5714-5759**.
- **Template card text**: `$MADGRAPH_INSTALL/Template/NLO/Cards/run_card.dat:155-211` (binary-ish `.dat`; read with `sed`, not Read). Carries the human-facing comments.
- **Fixed-order cut application**: `$MADGRAPH_INSTALL/Template/NLO/SubProcesses/cuts.f` (`passcuts_user`, line 10) — header line 7-9 states the hard rule: **"ONLY IRC-SAFE CUTS CAN BE APPLIED OTHERWISE THE INTEGRATION MIGHT NOT CONVERGE."**
- **PDG-cut fortran backstop**: `Template/NLO/SubProcesses/setcuts.f:108-144`.

## The NLO cut set (banner.py:5715-5759 — param inventory + coordinate; read each default fresh at its line)

Cache the inventory + the version-stable semantics (enum meanings, the `<0 = no cut` convention, which params are `cut`/hidden), NOT the numeric defaults — they drift and a stale one reads as valid. Read a default at its `add_param` line when load-bearing.
Jet (FastJet-clustered): `jetalgo` (1=kT, 0=C/A, -1=anti-kT), `jetradius`, `ptj` (cut), `etaj` (cut; <0 = no cut), `gamma_is_j`.
Lepton (applied to *recombined/dressed* leptons): `ptl` (cut), `etal` (cut; <0 = no cut), `drll`, `drll_sf`, `mll` (5724), `mll_sf` (5725 — ships a NON-ZERO built-in same-flavor floor; read it).
Fermion-photon recombination: `rphreco`, `etaphreco`, `lepphreco`, `quarkphreco` (bool).
Photon isolation (hep-ph/9801442 smooth-cone): `ptgmin` (cut), `etagamma`, `r0gamma`, `xn`, `epsgamma`, `isoem` (5730-5735).
Massive-PDG per-particle cuts (dicts, `include=False`): `pt_min_pdg`, `pt_max_pdg`, `mxx_min_pdg`, `mxx_only_part_antipart` (default `{default:False}`). These translate to hidden fortran arrays `pdg_cut`/`ptmin4pdg`/`ptmax4pdg`/`mxxmin4pdg`/`mxxpart_antipart` in `update_system_parameter_for_include` (banner.py:5962, the per-include translation method on the validity path — NOT inside `check_validity`'s body itself).
Hidden: `maxjetflavor` (5736).

## How the NLO set differs from LO (in-slice claim only on the NLO side)

The NLO class registers ONLY the cuts above. The familiar LO basic cuts — `ptb`/`etab`/`drbb`/`mmbb` (b-specific), `mmjj`/`mmnl`/`ht`, per-particle energy cuts, `cut_decays`, `xptj`/`xetamin`/`deltaeta` matching-style cuts — are NOT registered in `RunCardNLO` (grep-confirmed absent across the NLO class body 5594-5760). The reason source gives is IR-safety, not feature parity:

- **No bare-parton / b-specific cuts.** cuts.f:22-26: "when using a 5-flavour scheme calculation (massless b quark), no b-tagging can be applied." Combined PDG channels share one PDG set, so flavour-tagged parton cuts aren't available. A b is just a jet constituent at NLO.
- **No `cut_decays`.** Decay products are not separately cut at NLO.
- **No individual-parton pt/eta cut.** Partons enter only via the FastJet jet, never cut individually (would be collinear-unsafe).

Exact LO cut catalog and which LO params exist via which mechanism are ma-kinematic-cuts-consultant's slice — do not assert the LO side from this page.

### Dilepton invariant-mass cut name split LO vs NLO (verified v3.7.1)

Class boundaries: `RunCardLO` = banner.py:4187, `RunCardNLO` = banner.py:5594.

- **LO** (RunCardLO): `mmll` (banner.py:4368, `cut='ll'`) + `mmllmax` (4372). NO `mll`/`mll_sf`. Read defaults at those lines.
- **NLO** (RunCardNLO): `mll` (banner.py:5724, `cut=True`) + `mll_sf` (5725, `cut=True`). NO `mmll`/`mmllmax` (grep-confirmed: `mmll` appears ONLY at 4368/4372, inside RunCardLO). Read defaults at 5724/5725.
- Template comments (`Template/NLO/Cards/run_card.dat:178-179`): `mll` = "Min inv. mass of all opposite sign lepton pairs"; `mll_sf` = "Min inv. mass of all opp. sign same-flavor lepton pairs". So `mll_sf` is the same-flavor OS analogue; NOTE the NLO card ships a NON-ZERO `mll_sf` built-in same-flavor cut (read its default at 5725) while `mll` defaults to no all-flavor cut — a silent same-flavor dilepton floor to be aware of.
- Consequence (NLO-side ownership fact): `mll`/`mll_sf` are NLO-only names; `mmll`/`mmllmax` are LO-only. Putting `mmll` in an NLO run_card, or `mll` in an LO run_card, hits an unknown-parameter path. The LO-side reject text/behavior ("WARNING invalid set command … mll", discarded) is ma-kinematic-cuts / ma-interface territory — this page only owns that the NLO card carries `mll`/`mll_sf` and NOT `mmll`.

### Photon-isolation param visibility LO vs NLO (Frixione smooth-cone, hep-ph/9801442)

The NLO card exposes ALL six photon-iso params as non-hidden (banner.py:5730-5735): `ptgmin` (`cut=True`), `etagamma`, `r0gamma`, `xn`, `epsgamma`, `isoem` — read their defaults at 5730-5735. Template text at run_card.dat:194-198 (`R0gamma`/`xn`/`epsgamma` cite eq.(3.4) of hep-ph/9801442).
At LO (RunCardLO) the shape params `r0gamma`/`xn`/`epsgamma`/`isoem` carry `hidden=True` (banner.py:4414-4417); `ptgmin` is NOT hidden at LO (4413, `cut='aj'`). So: `r0gamma`/`xn`/`epsgamma` are hidden at LO and visible at NLO; `ptgmin` is visible at BOTH. LO hidden-flag mechanics are kinematic-cuts' slice; reported here only as the NLO-side corroboration.

### FKS_params.dat (pointer only — FKS internals = fks slice)

`Template/NLO/SubProcesses/FKS_params.dat` exists as a symlink → `../Cards/FKS_params.dat` (verified). Header (FKS_params.dat:2-6): "sets the different technical parameters intrinsic to the FKS program and which controls the behaviour of the code at run time. The common user should not edit this file and only experts should venture editing." First block = IR-pole comparison thresholds (OLP-vs-MadFKS relative pole difference). It is NLO-output-only and holds FKS runtime technical parameters, NOT user cuts. Deep content → fks slice.

## IR-safety mechanisms visible in source

1. **Jets are clustered first, then cut.** `passcuts_jets` (cuts.f:487) calls `amcatnlo_fastjetppgenkt_etamax_timed` (cuts.f:553) with `palg=jetalgo, rfj=jetradius, sycut=ptj, etaj`, then requires `njet .ne. nQCD .and. njet .ne. nQCD-1 → fail` (cuts.f:559). The cut is on the clustered jet, so a soft/collinear extra parton (which clusters into the same jet) does not flip the cut decision. This is what makes `ptj` IR-safe. Also cuts.f:515-528 kills configs with >1 ultra-soft parton (`|E/E_beam|<1e-8`) to tame Real-emission numerical instability.
2. **Leptons are cut after photon recombination.** `passcuts_user` recombines photons into fermions (`recombine_momenta`, cuts.f:84) BEFORE calling `passcuts_leptons` on `p_reco`/`ipdg_reco` (cuts.f:88, function at 622). So `ptl`/`etal`/`drll`/`mll` act on *dressed* leptons — a collinear photon emission doesn't change the lepton's passing status. `rphreco=0` disables recombination (template:182).
3. **Photon isolation = smooth-cone (Frixione), not fixed cone.** `passcuts_photons` (cuts.f:189) per hep-ph/9801442; collinear-safe by construction. Skipped entirely when `gamma_is_j=True` (photons clustered as jets, cuts.f:243) or `ptgmin=0` (early return, cuts.f:249-251 region). Template:189-191 mirrors this.
4. **Per-particle cuts restricted to MASSIVE, non-jet/lepton/photon particles.** `passcuts_pdgs` (cuts.f:713) loops `nincoming+1..nexternal-1` (line 736 — **excludes the last particle** because the n-body FKS counter-event has one zeroed momentum). The eligibility is enforced in `setcuts.f`:
   - **`setcuts.f:117`**: `pmass(i).eq.0d0 → stop 1` ("only massive particle can be included").
   - **`setcuts.f:125`**: `is_a_lp/lm/j/ph → stop 1` ("can not be used for jet/lepton/photon/gluon").
   This is the IR-safe escape hatch for cutting on, e.g., a top or a Z by PDG — allowed because a massive colour/charge-neutral-under-recombination particle can't go soft/collinear in a way that breaks FKS cancellation. (NOTE: `setcuts.f:113/120` are the `cycle`/`is_a_lp` *test* lines; the actual `stop 1` statements are at 117 and 125 in v3.7.1.)

## ickkw interaction with the jet cut (cuts.f:103-111, 513, 592, 605)

The cut path branches on `ickkw` (the merging mode, read from `run.inc`):
- `ickkw.ne.3`: ordinary `passcuts_jets`.
- `ickkw.eq.3` (FxFx): `passcuts_fxfx` (cuts.f:448) instead — uses `amcatnlo_fastjetdmerge`; the ordinary ptj/jet cut is bypassed. (FxFx also force-sets `jetalgo=jetradius=1` at card-validate — see [[runcardnlo-defaults-and-ickkw]] / [[fxfx-ickkw3-lifecycle]].)
- `ickkw.eq.4` (UNLOPS): `passcuts_jets` returns immediately (cuts.f:513); the pT cut is instead the special pythia cut `pythia_UNLOPS` in `passcuts_unlops_jv` (cuts.f:592-603).
- `ickkw.eq.-1` (NNLL jet-veto): `passcuts_unlops_jv` requires exactly one QCD parton (`nQCD.ne.1 → stop`, cuts.f:607-611) and vetoes if `pt(parton) > ptj` (cuts.f:612).

## fixed-order vs NLO+PS and the cut set

The cut *code* is the same template `cuts.f` regardless of AskRunNLO mode (fixed_order ON vs OFF). What the mode changes is the *softness advice*, not the parameters: template:161-162 — "When matching to a parton shower, these generation cuts should be considerably softer than the analysis cuts." So at NLO+PS (shower on) generation cuts are deliberately loose and the analysis cut is reapplied downstream; at fixed-order the run_card cut IS the fiducial definition. The AskRunNLO mode lives in [[askrunnlo-dialog-and-showers]]; this page owns only the cut block's reaction.

## Cautions / probe-verified findings

- **Python massless-PDG guard (banner.py:5977 `if any(pdg in pdg_to_cut for pdg in …)`, comment 5978, raise at 5979) has a string-vs-int gap on the dict path.** The guard lives in `update_system_parameter_for_include` (5962), not `check_validity`'s body. `pdg_to_cut` (built at 5965-5966) comes from `pt_min_pdg`/`pt_max_pdg`/`mxx_min_pdg`/`mxx_only_part_antipart` dict *keys*, which are **strings** (`'21'`), but the guard tests `pdg in pdg_to_cut for pdg in [21,22,11,13,15]+list(range(maxjetflavor+1))` with **integers**. `21 in {'21'}` is `False` (re-probed v3.7.1: `RunCardNLO()['pt_min_pdg']={'21':50.}; check_validity()` raises NO exception; `21 in {'21'}` → False). So a user cutting a gluon/quark/photon/lepton by PDG passes the Python validation silently. The negative-PDG guard at 5972 uses `int(pdg)<0` and DOES work. The comment at 5980 ("this will double check in the fortran code") is load-bearing: the REAL enforcement is `setcuts.f:117/125` (`stop 1` on massless or jet/lepton/photon). Net effect: an IR-unsafe PDG cut is caught at COMPILE/RUN time (fortran `stop`), not at card-write time. Don't tell a user "the card validator will reject it" — it won't via the dict path; the run aborts later.
- `etaj`/`etal`/`etagamma` `<0` means NO cut (template:168,175; cuts.f:667 gates `etal.gt.0d0`). A user expecting eta=0 to mean "central only" gets the opposite (no cut).
- `gamma_is_j=True` (the default) silently disables ALL photon-isolation params (ptgmin/r0gamma/xn/epsgamma) — photons are jet constituents. To get isolated-photon fiducial cuts you must set `gamma_is_j=False` (and `create_default_for_process` auto-sets it False only for tagged-photon / no-QED-splitting processes — see [[runcardnlo-defaults-and-ickkw]]).
- `ptgmin=0` early-returns the whole photon block (template:191 "When ptgmin=0, all the other parameters are ignored").

## Expensive probe-candidates (not run)

- Confirm `setcuts.f:117` `stop 1` actually fires at runtime for a real NLO process with `pt_min_pdg={'21':50}` (needs full `output`+`compile`+`launch` of e.g. `p p > Z [QCD]`). Cheap Python probe already confirmed the Python guard does NOT fire; the fortran stop is unverified at runtime.
- Confirm the `njet .ne. nQCD-1` IR-safe jet acceptance does not reject Born-level events for a 0-jet Born (e.g. `p p > t t~ [QCD]`) under the default `ptj` (read its default in the NLO cut block).
