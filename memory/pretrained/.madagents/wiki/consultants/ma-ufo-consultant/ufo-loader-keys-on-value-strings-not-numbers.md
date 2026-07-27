---
description: The loader fixes MODEL CONTENT (which couplings/interactions survive, which are merged or dropped) from the AUTHORED value STRINGS at load time — str(coupling.value), the dict-vs-string TYPE — before any param_card numeric value is read. The evaluated number enters only at runtime, and numeric-keyed pruning (zero/identical detection on evaluated values) is restriction's job, out of slice. Routes "I changed a coupling NUMBER and the model structure didn't change" / "structure changed without a number change."
---

# The loader keys model content on value STRINGS, not on evaluated numbers (import_ufo.py, v3.7.1)

Generalization page. Three instance pages each observe a piece of the same mechanism; the principle catches the whole class and the loader↔restriction boundary none of them states alone.

**Principle.** `import_full_model` / `UFOMG5Converter` decide WHICH couplings, interactions, and (in loop mode) pole-pieces end up in the loaded `Model` purely from the **authored `Coupling.value`** — its literal STRING (`str(coupling.value)`) or its Python TYPE (string vs Laurent dict). **No param_card numeric value is read at this stage.** The evaluated number enters only later: `Model.set_parameters_and_couplings(param_card=...)` is called from `import_model`'s restriction/CMS path (`import_ufo.py:283`, and `RestrictModel.restrict_model` at `:2390` reads the card), AFTER `import_full_model` has already fixed model content. So:

- A coupling whose authored `value` string is not literally `'0'` SURVIVES the loader regardless of what it evaluates to — even if the param_card drives it to exactly 0 at runtime.
- The loaded model structure (vertex/interaction/coupling membership, Lorentz merges) is a function of the `.py` files ONLY, never of card numbers.
- Anything that prunes/merges on EVALUATED numbers (zero couplings, numerically-identical couplings, small-value-as-zero) is **restriction slice** (`RestrictModel`), a separate stage on a separate key.

This is the structural reason behind the lead playbooks `removed-coupling-not-small` and `coupling-vertex-viability`: "set a coupling to zero" (card number → 0, structure intact, diagrams still generate) is a fundamentally different model state from "the coupling was removed" (restriction deleted the param+coupling+vertex). The dividing line is exactly load-time-string vs evaluated-number.

## The three string/type-keyed loader decisions (all in `UFOMG5Converter`, all pre-card)

1. **ZERO-collapse** — `optimise_interaction` (`import_ufo.py:686`). On first call it seeds `coups['0'].append('ZERO')` (`:693`) and builds `iden_couplings` over `str(coupling.value)` (`:695`); per interaction, any coupling resolving to `'ZERO'` is `del`-eted (`:707-708`). The key is the LITERAL string `'0'` — a coupling whose `value` is an expression that merely *evaluates* to 0 is NOT dropped. Instance: `ufo-vertex-presence-vs-coupling-value.md` (set-to-zero ≠ removed); mechanism owner `ufo-vertex-to-interaction-conversion.md`.

2. **Identical-coupling collapse** — same `optimise_interaction` (`:691-708`). Couplings sharing an identical `str(coupling.value)` are mapped to a single representative (the first). String-equality, before any evaluation — distinct from restriction's numeric version (below). Instance/owner: `ufo-vertex-to-interaction-conversion.md`.

3. **Dict-valued coupling handling by mode** — `analyze_couplings` (`import_ufo.py:2204-2226`). Keys on the Python TYPE `isinstance(coupling.value, dict)`: in a loop model each non-`'ZERO'` `coupling.pole(poleOrder)` becomes a copied coupling (`:2210-2223`, lowercase `_1eps`/`_2eps` suffix); in a TREE model the dict-valued (Laurent) couplings are SILENTLY FILTERED OUT — `[c for c in couplings_list if not isinstance(c.value, dict)]` (`:2226`). Type-of-the-string, still no number. Instance/owner: `ufo-expression-shortening-and-event-dependence.md`.

## The contrast that fixes the boundary — restriction keys on EVALUATED numbers

`RestrictModel.detect_identical_couplings` (`import_ufo.py:2525`) operates on `self['coupling_dict'][name]` — the **numerically evaluated** coupling values (the param_card has been read by `set_parameters_and_couplings`). It tests `value == 0` (`:2549`), `abs(value) < 1e-13` "treated as zero" (`:2552-2556`), `abs(value) < 1e-10` (re-run strict, `:2557`), and merges via `limit_to_6_digit` numeric rounding (`:2541-2547`). This is the SAME conceptual operation as loader leg 1/2 (zero + identical collapse) but on a DIFFERENT key (number, not string) at a DIFFERENT stage (restriction, not load) — and it is **out of my slice**. Confusing the two is the trap: the loader's `'0'`-string drop and restriction's numeric-zero drop look alike but fire on different inputs and at different times.

## Why the principle catches more than the instances

The instances each name one decision. The principle predicts the answer for ANY "I changed a coupling number / param_card value and the model structure did/didn't change" question, including couplings/models the instance pages never named:
- "I set my WC / coupling to 0 in the card — why do the diagrams still generate?" → load-time membership is string-keyed; the number is read after content is fixed. Structure unchanged is EXPECTED; only the amplitude collapses.
- "Two couplings have the same numeric value at my benchmark but the loader kept both?" → loader collapses only on identical SOURCE STRINGS; numeric coincidence is restriction's `detect_identical_couplings`, a later stage.
- "A coupling literally `value='0'` vanished from the loaded model even with no restriction?" → that IS the loader's `'0'`-string ZERO-collapse, a load-time drop independent of any card.
- "My loop model's Laurent couplings disappeared when I loaded it as a tree model?" → the `isinstance(...,dict)` tree-filter at `:2226`, a TYPE decision, silent and card-independent.
- The diagnostic for the whole class: a STRUCTURE change (membership/merge/drop) traces to a `.py`-file edit (string/type) or to restriction; it NEVER traces to a param_card number. A NUMBER change moves amplitudes, never the loaded structure.

## Boundary
- Numeric-keyed pruning/merging (zero detection, identical-to-6-digits, small-as-zero) on EVALUATED param_card values is **restriction slice** (`RestrictModel`, `import_ufo.py:2366+`). I own the loader-stage string/type keys only.
- Where the param_card number goes once read, and the σ consequence of a small/zero coupling, is param-card + phase-space slices.
- The one place the loader reads a numeric literal is a particle's own `float(value)` attribute default (`:1278`, charge/mass numeric cast) — NOT a coupling-content decision; it does not violate the principle.

## Caution
- "Set the coupling to zero" (card number → 0) and "the coupling is `value='0'` / removed" are THREE distinct states: (a) card-zero → vertex+coupling present, diagrams generate, amplitude → 0/residual (load-time string ≠ `'0'`); (b) authored `value='0'` → loader ZERO-collapse drops it at load, no card needed; (c) restriction removal → param+coupling+vertex gone, NoDiagramException / silent subprocess drop. Don't conflate.
- The loader-stage identical/zero collapse (`:686`) and the restriction-stage version (`:2525`) share intent but key on string vs number — never cite one for the other.
