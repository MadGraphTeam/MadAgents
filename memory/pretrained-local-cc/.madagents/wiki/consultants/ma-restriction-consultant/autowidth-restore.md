---
description: modify_autowidth callback and the auto-width restore step that re-marks DECAY params as 'auto' after pruning (import_ufo.py v3.7.1)
---

# Auto-width collection and restore

## modify_autowidth callback (2386-2388)
```
def modify_autowidth(self, cards, id):
    self.autowidth.append([int(id[0])])
    return math.log10(2*len(self.autowidth))
```
Passed as `auto_width=self.modify_autowidth` into `set_parameters_and_couplings` at 2407-2409. When a DECAY entry in the restrict card has the value `'auto'`, this callback fires: it records the lhacode (as `[int(id[0])]`) into `self.autowidth` and returns a small NONZERO sentinel numeric width (`log10(2*N)`). `self.autowidth` initialised to `[]` in `default_setup` (2384).

Why the sentinel must be nonzero: if auto-width returned 0, the width would be treated as a zero parameter and the particle's width set to 'ZERO' / decay interactions could be pruned. The `log10(2*N)` placeholder keeps the width nonzero through the zero/identical detection so the decay structure survives restriction.

## Restore step (2467-2475)
After all pruning/merging, loops `self['parameters'][('external',)]`; for each param whose `lhablock.lower()=='decay'` and whose `lhacode` is in `self.autowidth`, sets:
- `parameter.value = 'auto'`
- and in `parameter_dict`: key `parameter.name` if present, else `name[4:]` if name starts with `mdl_`, else `raise Exception`.

This re-marks the width as 'auto' so the downstream compute-widths / auto-width recompute path (madwidth slice) has something to recompute. Without this collect+restore, the placeholder numeric width would persist and the auto path would have nothing to trigger on.

## Dormant for ALL bundled models (statically verified)
The callback fires only when a DECAY value is literally `'auto'`: `model_reader.py:90` gates it on `str(param.value).lower() == 'auto'` → `param.value = auto_width(...)`. NO bundled restrict card sets any DECAY width to `'auto'` — `grep -riwn auto $MADGRAPH_INSTALL/models/*/restrict_*.dat` returns only comment-header lines ("## Width set on Auto will be computed ...", e.g. 2HDM5F_NLO/restrict_noL.dat:5, 2HDMtypeII/restrict_nobmass.dat:5), never a DECAY value. The shipped DECAY blocks carry numeric widths (e.g. sm/restrict_default.dat:29-33 — read the magnitudes there). So for every bundled model, `modify_autowidth` is NEVER invoked during restriction, `self.autowidth` stays `[]`, and the restore loop (2467-2475) is a no-op. The entire collect-and-restore mechanism only fires when a USER supplies a custom restrict (or sibling param) card with an `'auto'` DECAY value. (Config-content + trigger-line fact, statically verified; not a runtime prediction.)

## Sibling param_*.dat reload re-fires the callback AFTER restore (ordering caution)
The final step of `restrict_model` (2491-2496) re-calls `set_parameters_and_couplings` with `auto_width=self.modify_autowidth` if a sibling `param_<...>.dat` exists (the `restrict`→`param` name swap). This SECOND callback pass appends to `self.autowidth` again — but it runs AFTER the restore loop (2467-2475). So an `'auto'` DECAY value present only in the sibling `param_*.dat` (not in the original restrict card) is collected into `self.autowidth` yet never re-restored to `'auto'`, because the restore loop already executed. The placeholder `log10(2*N)` numeric width from the second pass would persist. Auto-widths originating in the restrict card itself are fine (collected in the first pass at 2407-2409, restored at 2467-2475); only sibling-introduced ones hit this gap. (Source-visible ordering. The swap is literally `param_card.replace('restrict', 'param')` on the FULL restrict-card path, 2491. NO bundled restrict card has a swap-sibling — `for f in models/*/restrict_*.dat; do test -f "$(echo $f|sed 's#/restrict_#/param_#')"; done` matches NONE across all 30 bundled restrict cards. `taudecay_UFO/param_card.dat` exists but is NOT a swap-sibling — that model ships no restrict card, so step 16 never runs there. So step-16 sibling reload never fires for any bundled model, and this gap can only be triggered by a user-supplied sibling. Not a runtime claim.)

## Why the sentinel survives the prune/merge passes (2615-2644, 2709-2744)
Two source-level guarantees keep an auto-width from being pruned or merged between callback (2409) and restore (2468):

1. **`detect_special_parameters` only flags `==0` / `==1`** (2621-2624): `if value == 0 ... elif value == 1`. The sentinel `log10(2*N)` is `0.301` (N=1), `0.602` (N=2), `0.699` (N=3)... — never 0 or 1 for any N≥1. So an auto-width never enters `null_parameters`/`one_parameters`, hence `fix_parameter_values` never converts it external→internal nor prunes it. (The nonzero sentinel is what dodges the `==0` test; this is the mechanism behind "must be nonzero" above.)

2. **`detect_identical_parameters` exempts the DECAY block entirely** (2726-2727): `if param.lhablock.lower() == 'decay': continue` — DECAY-block params are skipped BEFORE the `(lhablock, value)` collision key is built (2728), so NO width parameter is ever a merge candidate. Two particles with identical numeric widths are never merged; and an auto-width sentinel can never collide with another width. This is a STRONGER guarantee than the sentinel-value argument: even coinciding sentinels can't merge, because width merging is categorically off. (Note it also `continue`s on value in `[0,1,0.000001e-99,9.999999e-1]` at 2724 — but the decay guard at 2726 is the one that protects widths specifically.)

Net: width parameters are categorically exempt from identical-merge, and a nonzero-sentinel auto-width is exempt from zero/one special-handling. The ONLY thing that can change an auto-width during restriction is the restore loop itself (2468), which re-marks it `'auto'`.

## Caution
`self.autowidth` stores `[int(id[0])]` (a one-element list), and the restore test is `parameter.lhacode in self.autowidth` — so lhacode must match the list form. Auto-width survival depends entirely on this collect-then-restore; it is NOT a property of the width value itself during restriction.

A width set to a literal numeric `0` in the restrict card (NOT `'auto'`) is a different story: it IS detected as null (2621) and its particle width becomes ZERO — but that is the intended zero-width restriction, not an auto-width loss. Auto-width loss only happens via the sibling-reload ordering gap above (callback re-fires after restore), never via the special/identical passes.
