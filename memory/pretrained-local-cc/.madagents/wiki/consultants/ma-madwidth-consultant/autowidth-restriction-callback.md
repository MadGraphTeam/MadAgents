---
description: How AUTO width values survive model restriction — the modify_autowidth callback, its log10 placeholder, the post-restriction restore loop in RestrictModel, and the three distinct auto-width placeholders (load=0.0, restriction=log10(2N), compute-time=1).
---

# AUTO width restriction callback (v3.7.1)

## The two `auto` handlers in set_parameters_and_couplings
`models/model_reader.py:58` `set_parameters_and_couplings(..., auto_width=None)`:
- **With callback** (restriction path), 90-91: for each `decay` block param whose value is the string `'auto'` (case-insensitive, `str(param.value).lower()=='auto'`), `param.value = auto_width(param_card, param.lhacode)`. The callback both records the pid AND returns a numeric placeholder so the model can finish evaluating.
- **Without callback** (normal load), 186-187: `if isinstance(value,str) and value.lower()=='auto': value = '0.0'`. So outside restriction, an `auto` width simply evaluates to 0.0 — the particle is treated as zero-width until `compute_widths` overwrites the card.

## modify_autowidth callback
`models/import_ufo.py:2386`:
```python
def modify_autowidth(self, cards, id):
    self.autowidth.append([int(id[0])])
    return math.log10(2*len(self.autowidth))
```
- Appends the lhacode (as `[pid]`) to `self.autowidth`.
- Returns `log10(2*N)` where N is the running count of auto-widths collected so far — a deliberately nonzero, distinct placeholder (NOT a physical width). Purpose: let restriction's parameter machinery run without dividing-by-zero or merging the auto particles' widths as "identical zero" params.

## Restore loop after restriction
`models/import_ufo.py:2390` `restrict_model(...)`:
- Calls `set_parameters_and_couplings(param_card, ..., auto_width=self.modify_autowidth)` at 2407-2409 — this populates `self.autowidth`.
- After all restriction steps (coupling merge, param fix, identical-param merge), the restore loop at 2464-2473 (comment "restore auto-width value" 2464; loop `for parameter in self['parameters'][('external',)]:` 2467; gate `parameter.lhablock.lower() == 'decay' and parameter.lhacode in self.autowidth` 2468): set `parameter.value = 'auto'` (2469) and write `'auto'` back into `parameter_dict` (handling the `mdl_` prefix at 2470-2473, `else: raise Exception` 2474-2475). This re-installs the literal string so the written restricted param_card shows `DECAY <pid> auto`, ready for later `compute_widths`.
- A SECOND `set_parameters_and_couplings(..., auto_width=self.modify_autowidth)` runs at 2491-2496 if a sibling `param_card.dat` (restrict→param) exists, to set default values — again preserving auto handling.

## Three distinct `auto` placeholders — don't conflate
The literal `auto` width string is replaced by a different stand-in at three different moments:
1. **Normal model load** → `'0.0'` (model_reader.py:186) — zero-width until recomputed.
2. **During restriction** → `log10(2*N)` (import_ufo.py:2388) — nonzero, distinct-per-pid placeholder so coupling/param merging doesn't divide-by-zero or merge auto particles as "identical zero"; then restored to the `auto` string (restore loop, 2468-2473).
3. **At compute_widths time** → `1` (float) — `do_compute_widths` (madgraph_interface.py:9847-9860) AND `compute_widths_SMWidth` (10036-10049) scan `param_card['decay']`, set any `param.value == "auto"` to `1` with `format='float'`, and rewrite the card (to `output` if set, else `path`) before numeric eval. So a card still flagged `auto` is given a unit dummy width for the integration scaffold, which the survey result then overwrites via `update_width_in_param_card`.

## Why the placeholder matters
Without restoring the string, restriction would freeze the log10 placeholder as the width. The collect-then-restore pattern keeps auto-flagged widths as `auto` through restriction so compute_widths can replace them at runtime — at which point placeholder (3) takes over as the integration-time dummy.

## Boundary
- The restriction ALGORITHM (pruning zero params/couplings, merging identical) is the restriction slice. This page owns only the auto_width hook into it.
- The param_card format/SLHA conversion of the written `auto` line is the param-card slice.
