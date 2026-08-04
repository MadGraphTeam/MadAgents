---
description: launch-time interactive-switch gating for Rivet — available_module add (needs rivet_path AND PY8), get_allowed_analysis exposure, set_default_analysis never auto-picks Rivet, bidirectional consistency_shower_analysis/consistency_analysis_shower forcing the Rivet<->Pythia8 coupling.
---

# Launch-time switch gating for Rivet (madevent_interface.py)

This is the `launch` interactive-switch layer — whether `Rivet` is OFFERED as an `analysis=` switch option and the hard Pythia8 coupling. It is UPSTREAM of and distinct from `do_rivet`'s card resolution (do_rivet-flow.md) and from `init_rivet`'s card-editor gate (install-and-config.md `has_rivet`). Three independent gates can all suppress Rivet.

## available_module 'Rivet' (madevent_interface.py:535-539)
- `if options['rivet_path']:` AND `'PY8' in self.available_module` => `self.available_module.add('Rivet')` (535-537).
- rivet_path set but NO PY8 => `logger.warning("Rivet program installed but no parton shower with hepmc output detected.\n    Please install pythia8")` (538-539). NO Rivet module.
- So the switch-level availability needs BOTH a configured rivet_path AND Pythia8 — Rivet runs only on Pythia8 HepMC. (Parallel to the Delphes block at 530-534 which accepts PY6 or PY8; Rivet is PY8-only.)

## get_allowed_analysis (745-761)
- Builds `self.allowed_analysis` once (cached via `hasattr` guard, 745-746).
- Appends 'ExRoot'/'MadAnalysis4'/'MadAnalysis5' then `if 'Rivet' in self.available_module: append('Rivet')` (755-756).
- If any analysis allowed, also appends 'OFF' (758-759). So 'Rivet' appears in the `analysis=` switch choices ONLY when the available_module gate above passed.

## set_default_analysis (807-822) — Rivet is never the DEFAULT
- Default `switch['analysis']` priority: MA4 (if plot_card.dat) -> MA5 (if a madanalysis5_*_card.dat) -> ExRoot -> else `OFF` (if any analysis allowed) -> else `'Not Avail.'`.
- Rivet is NOT in this chain: the default analysis switch is never auto-set to 'Rivet'. Even with Rivet available, the user must explicitly pick `analysis=Rivet` (or `--analysis=Rivet`); otherwise it defaults to OFF. (Contrast: a present rivet_card.dat drives the post-shower `rivet --no_default` auto-call independently — see do_rivet-flow.md run-sequence wiring. The switch default and the card-presence auto-call are different mechanisms.)

## Bidirectional Rivet<->Pythia8 consistency (782-808)
Dispatched BY NAME from the switch machinery: `extended_cmd.py:2821-2822` calls `consistency_<keyA>_<keyB>(valA, valB)` whenever the user changes one switch, to repair the other.
- `consistency_shower_analysis(vshower, vanalysis)` (782-792): if `vshower != 'Pythia8' and vanalysis == 'Rivet'` => returns `'OFF'` — setting shower to anything but Pythia8 while analysis=Rivet FORCES analysis back to OFF.
- `consistency_analysis_shower(vanalysis, vshower)` (794-804): same condition => returns `'Pythia8'` — setting analysis=Rivet while shower!=Pythia8 FORCES shower to Pythia8.
- Net: the two switches are pinned together — you cannot end an interactive switch session with analysis=Rivet and a non-Pythia8 (or OFF) shower. One of them gets rewritten.

## Boundary
- This is the SWITCH layer (what `launch` offers and auto-repairs). It does not run Rivet — that is do_rivet (do_rivet-flow.md). A run that bypasses the switch (e.g. direct `rivet RUN` command, or the post-shower auto-call) does not go through these gates; do_rivet's own card/path resolution applies there.
- The PY8 availability detection (what puts 'PY8' in available_module) is the pythia8-interface slice's territory; here I only consume the resulting `'PY8' in self.available_module` boolean.
