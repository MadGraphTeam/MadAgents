---
description: The event must be showered and hadronized. It goes past the matrix element into Pythia8.
---

# Pythia8 shower / hadronization configuration — fan-out

Any "set up / configure the Pythia8 shower" request spans **four slices**. Route each sub-question to its owner; the PY8-card content in particular is a recall trap — several commonly-cited "defaults" (Tune:pp=14, JetMatching:qCut=30, nJetMax=2) are **not** what MG's shipped cards actually set.

## Owner map

- **`ma-pythia8-interface-consultant`** — pythia8_card.dat location (`<PROC_DIR>/Cards/pythia8_card.dat`) + native `Setting = Value` syntax; the shipped default card content; `HEPMCoutput:file` / `HEPMCoutput:scaling` (the only two `HEPMCoutput:*` params); shower_card ME-correction defaults; `set pythia8_card …` launch-dialogue edits and pre-edited card path; tau `mayDecay` passthrough; post-shower σ read-back. Also owns how the launch dialogue surfaces a missing Pythia8 install (greys out `PY8`).
- **`ma-matching-consultant`** — the MLM `JetMatching:*` params the PY8 card carries under `ickkw=1`, their run-side defaults/resolution, and the matched-σ veto mechanism (post-shower matched σ is the physical value).
- **`ma-amcatnlo-consultant`** — the NLO **`parton_shower`** run_card parameter (values, code default, the `shower=` override), which is RunCardNLO-only. LO has no shower-program selector in the card.
- **`ma-installation-consultant`** — `install pythia8` (fetch/compile/config keys), and the upstream config-key condition when Pythia8 is absent.

## Doc-myth / recall traps (each → the owning consultant's page)

- **No `Tune:pp` default.** MG's shipped LO default card carries **no** `Tune` line at all — Pythia's own compiled default tune governs unless the user adds one. `tune_pp=14`/`tune_ee=7` exist only as dead, commented `add_param`s in `shower_card.py`. → pythia8-interface `py8-card-defaults`.
- **MLM `JetMatching` "defaults" are fabricated.** Card defaults are `qCut = -1.0` and `nJetMax = -1` (sentinels → auto-resolved at run to `1.5*xqcut` and `max_n_matched_jets`), not `30`/`2`. `JetMatching:scheme=1` is **force-set** at run (not a user card default), and "kt-MLM" is the meaning of `doShowerKt=off`, a distinct knob — not `scheme`. `qCut` "must be > xqcut" is wrong: the reference is `1.5*xqcut` and a violation only logs an error (no abort). → matching `mlm-py8-bridge`.
- **`hepmc@<dir>` is broken in 3.7.1** (real, not just 3.7.0): `store_result()` uses `hepmc_fileformat` unconditionally on the moveHEPMC path but only assigns it inside the compressHEPMC branch → `UnboundLocalError`. **Working form is `hepmc.gz@<dir>`.** `auto`→hepmc.gz and `autoremove`→hepmcremove are pre-aliases; the `.hepmc.fifo` extension is a documented convention, **not** code-validated. → pythia8-interface `hepmc-output-and-paths`.
- **`HEPMCoutput:scaling`**: source documents only `1.0`=mb and `1.0e9`=pb (default → pb); `1.0e12`=fb is arithmetically consistent but **not in source**. Hidden param, but always written to the operative card. → pythia8-interface.
- **`parton_shower` `shower=` override is interactive-only.** `shower=PYTHIA8` rewrites the NLO card's `parton_shower` **only** when card-editing is reached — under `-f`/scripted mode the override is gated out, so the card's own value (code default `HERWIG6`) governs and MG showers with that. The allowed-value list (`HERWIG6/HERWIGPP/PYTHIA6Q/PYTHIA6PT/PYTHIA8`) is enforced at `run()`, **not** card-write — a bad name passes card-write and fails at launch. `create_default_for_process` flips the per-process written default to PYTHIA8 for FxFx-eligible processes. → amcatnlo `parton-shower-param-and-mcatnlo-linkage`.
- **`install pythia8` is not standalone.** It force-reinstalls `mg5amc_py8_interface` (`--force`) and may recursively pull in `lhapdf6`; sets both `pythia8_path` and `mg5amc_py8_interface_path`. Token is case-sensitive (`install Pythia8` fails). If Pythia8 is absent/stale, the `Pythia.h` sentinel fails and `pythia8_path` is **silently reset to None** — how the launch dialogue then surfaces that is pythia8-interface's ControlSwitch/available-module gate, not install's. → installation subtree.

## Cross-slice seams

- **install ↔ pythia8-interface**: install establishes only the upstream condition (missing header → `pythia8_path=None`); whether the shower step then hard-errors, greys out `PY8`, or skips is the pythia8-interface launch-menu gate.
- **matching ↔ pythia8-interface**: matching owns the run-side `JetMatching:*` defaults/resolution written into the PY8 card; the Pythia8-side *semantics* of a given `scheme` value is pythia8-interface.
- **amcatnlo ↔ fks/nlo-export/physics**: `parton_shower` selects which shower's MC@NLO counterterms are computed (structural linkage via `fortran_name='shower_mc'`); the counterterm internals are fks/nlo-export, and the physics-correctness of a shower/counterterm mismatch is physics.
