---
description: Four independent gates can each silently suppress Rivet (no offer / no run) — switch-availability, has_rivet card-editor, do_rivet card-presence, path-validity; the unified "why didn't Rivet run / why isn't it offered" map.
---

# Why Rivet did not run / is not offered (four independent suppression gates)

Rivet can be silently absent at FOUR independent layers, each keyed off a DIFFERENT input and each with its own no-op behaviour. A "why isn't Rivet offered / why didn't it run" question is not answered by any single layer — it needs the union below. None of these is a runtime-output prediction; all four are deterministic source branches (verified line-for-line, this v3.7.1 image). The diagnostic value is knowing *which* gate fired, because the fix differs per gate.

The gates fire in pipeline order (config-load -> launch switch -> card-editor init -> do_rivet execution). A run can pass some and be stopped by a later one.

## Gate 1 — path-validity (config load) — `madevent_interface.py:2159-2162`
- A configured `rivet_path` is REJECTED unless `<rivet_path>/bin/rivet` exists: `elif key == "rivet_path": if not os.path.exists(pjoin(path,'bin','rivet')): logger.info("No valid rivet path found"); continue`.
- Keyed off: the on-disk `rivet_path` pointing at a real `bin/rivet`. In THIS image rivet is uninstalled (HEPTools has no rivet/ dir, mg5_configuration.txt has no rivet_path line), so this gate drops rivet_path at load — see install-and-config.md.
- Effect: `self.options['rivet_path']` is not honoured downstream; Gate 2 then sees no rivet_path.

## Gate 2 — switch availability (`launch` only) — `madevent_interface.py:535-539`, `807-822`
- `available_module.add('Rivet')` requires BOTH `options['rivet_path']` truthy AND `'PY8' in self.available_module` (535-537). rivet_path-but-no-PY8 -> warning "Rivet program installed but no parton shower with hepmc output detected." (538-539), NO module.
- Rivet is NEVER the default `analysis=` switch (`set_default_analysis` 807-822 never picks it; defaults to OFF). User must explicitly `analysis=Rivet`.
- Keyed off: rivet_path AND PY8 availability. See launch-switch-gating.md for the bidirectional Pythia8 consistency coupling.
- Effect: Rivet not in the `analysis=` switch choices, and never auto-selected. NOTE: this gate is the SWITCH layer only — a present `rivet_card.dat` still drives the post-shower auto-call `rivet --no_default` (madevent_interface.py:2670) independently of the switch, so Gate 2 does NOT suppress the card-presence auto-run.

## Gate 3 — has_rivet card-editor init — `common_run_interface.py:5340-5343`
- `init_rivet`: `self.has_rivet = False; if not self.get_path('rivet', cards): return []; self.has_rivet = True`. Returns `[]` either way; the side-effect is `has_rivet` + the `fast_rivet` shortcut + `rivet_card`/`rivet_vars` registration.
- Keyed off: `rivet_card.dat` (or `rivet`/`rivet_card.dat`) being IN THE CARD SET `cards` — `get_path` (5109-5142) is a card-SET membership check, NOT a path/install check. So this gate is about whether the card is being managed in this card-editor session, independent of Gates 1/2.
- Effect: no Rivet entry in the interactive card editor, no `fast_rivet` shortcut.

## Gate 4 — do_rivet card-presence — `common_run_interface.py:2962-2969`
- At execution: if `Cards/rivet_card.dat` does not exist on disk:
  - `no_default=True` (the post-shower auto-call `rivet --no_default`, madevent_interface.py:2670) -> `return None`, SILENT SKIP (2963-2965). This is why a process dir with no rivet_card.dat simply runs no Rivet during `generate_events` with no error.
  - `no_default=False` (manual `rivet RUN`) -> copies `rivet_card_default.dat` -> `rivet_card.dat`, logs "No rivet_card found. Take the default one." (2967-2969), then proceeds.
- Keyed off: physical existence of `Cards/rivet_card.dat` at do_rivet time, AND the `no_default` flag of the invocation.
- Effect: the most common "Rivet didn't run during my scan" cause — no rivet_card.dat on disk + the auto-call's `--no_default` = silent no-op.

## Diagnostic table
| symptom | gate | fix |
|---|---|---|
| Rivet not offered in `launch` `analysis=` switch | 2 (or 1 upstream) | install rivet AND ensure PY8; explicitly pick analysis=Rivet |
| "No valid rivet path found" at startup | 1 | rivet_path must point at a dir with `bin/rivet` (i.e. actually install) |
| No Rivet section in the card editor | 3 | ensure rivet_card.dat is in the managed card set (`to_init_card`) |
| Scan/generate_events ran, no Rivet output, no error | 4 (`--no_default` silent skip) | ensure `Cards/rivet_card.dat` exists on disk |
| `analysis=Rivet` keeps flipping to OFF | switch consistency, not a suppression gate | shower must be Pythia8 (launch-switch-gating.md) |

## Boundary
- This maps which gate suppresses Rivet. It does NOT predict what happens once all gates pass and `run_rivet.sh` executes against an uninstalled rivet (env/fastjet-prefix failure) — that is a runtime claim, not made here (install-and-config.md notes it as caution).
- Whether `'PY8' in available_module` (Gate 2's PY8 half) is the pythia8-interface slice's territory; here only the boolean is consumed.

## Instances generalized
- launch-switch-gating.md — Gate 1/2 (switch availability + Pythia8 coupling).
- install-and-config.md — Gate 1 (path-validity) + the has_rivet card-set note.
- do_rivet-flow.md — Gate 3 (init_rivet) + Gate 4 (do_rivet card-presence skip).
