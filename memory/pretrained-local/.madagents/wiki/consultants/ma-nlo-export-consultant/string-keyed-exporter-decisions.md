---
description: NLO FKS exporter keys several behavior decisions on human-facing strings/names/conventions, not typed flags — each with a silent/fragile failure mode (Gmu scheme, perturbation_order brackets, proc[0]=='P', PDG-250 Chi).
---

# String/name/convention-keyed exporter decisions (v3.7.1)

## The principle
`export_fks.py` decides several behavior-determining things by inspecting **human-facing strings, model names, PDG conventions, or directory-name prefixes** rather than typed metadata or an explicit flag. Each such decision is fragile: it silently does the wrong thing (or raises) when the string/name/convention departs from the assumed form. This catches MORE cases than any single instance page's caution — it predicts the failure mode for *new* string-keyed decisions, model renames, and odd histories the instances never named.

Boundary: decisions keyed on **canonical/structured** data are NOT in scope and are robust. Example: `qcd_pos`/`qed_pos` from `'QCD'/'QED' in split_orders` (`:1305`-`:1308`) — `split_orders` is the authoritative model-emitted list, not a human-facing string, so it does not carry the fragility. The principle is specifically about strings a human typed or named.

## The instances (source-confirmed)
- **Renorm scheme from model name** — `write_numder_me:3070`: `if not 'Gmu' in self.model.get('name')` → alpha(MZ) template (+ alpha(MZ) warning); else Gmu template. No flag. A Gmu-renormalised model not named with the substring "Gmu" silently gets the alpha(MZ) template. (ewsudakov-me-writers.md.)
- **perturbation_order from process-string brackets** — `finalize:880`-`884`: `order = re.findall(r"\[(.*)\]", history.get('generate'))`, then `'QED' in order[0]` / `'QCD' in order[0]`. Read back out of the typed process string, not the matrix element. `order[0]` IndexError if no bracket present. (finalize-nlo-process-dir.md.)
- **P-dir discovery from name prefix** — `finalize:915`-`916`: `[proc for proc in os.listdir('.') if os.path.isdir(proc) and proc[0]=='P']`. Any directory whose name starts with `P` is treated as a subprocess dir for jpeg/html. Same heuristic recurs elsewhere. (finalize-nlo-process-dir.md, p-directory-layout.md.)
- **Goldstone-Chi count from PDG 250** — `get_sudakov_imag_power:2875`: `base_ids.count(250) - other_ids.count(250)`. The Z→Goldstone(Chi) imaginary-unit exponent is counted by hardcoded PDG 250; depends on the model defining 250 as the neutral goldstone. (ewsudakov-me-writers.md.)

## Cases beyond the instances
The principle predicts (these are failure-mode HYPOTHESES, not probe-verified runtime claims — the source-structural keying is the verified part):
- Any future renorm scheme added the same way (substring test on model name) inherits the silent-misclassification mode.
- A model loaded under a renamed/aliased name breaks the "Gmu" detection even if physically Gmu-renormalised.
- A `history` whose first `generate` carries no `[...]` bracket → IndexError at `finalize:881`.
- A non-subprocess directory named `P*` under SubProcesses gets swept into jpeg/html generation.
- A model that does not map Z→Chi at PDG 250 mis-counts the imaginary power.

## The move
When a dispatch asks "does the NLO output do X for model/process Y?" and X is one of: renorm-scheme template choice, perturbation_order in proc_characteristic, which dirs get jpeg/html, or the Z→Chi power — check the **actual string/name/convention for THIS input** (model name substring, the literal bracket in history, the dir names, PDG 250 presence). Do not reason from the canonical case; the decision is keyed on the string, so a non-canonical string gives a non-canonical answer.

## Instances generalized (kept)
- ewsudakov-me-writers.md — Gmu-name scheme keying + PDG-250 detail (kept; carries the numder/template specifics).
- finalize-nlo-process-dir.md — perturbation_order regex + P-dir `proc[0]=='P'` (kept; carries the finalize-step context).
- p-directory-layout.md — the `proc[0]=='P'` caution (kept).
