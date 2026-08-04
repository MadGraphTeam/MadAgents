---
description: The {pol} block parse step in extract_process (split, multiparticle-spin-uniform check, spin lookup) and the post-construction Process.check_polarization ambiguity guard (p p > Z{T} Z) — parse mechanics only; spin-letter semantics owned by polarization slice.
---

# Polarization parse step (v3.7.1) — parse mechanics only

Spin-letter→value mapping (T/L/R/A/G/H/Q/W/S/+-/0..3) is the **polarization slice's** territory. Here: the parse/validation step only.

## `{...}` block parse, extract_process (5082-5190)
- `'{' in part_name` (5082): `part_name, pol = split('{',1)`; `pol, rest = pol.split('}',1)`.
- **Spin lookup** (5086-5106): loop on `no_dup_name`:
  - `self._curr_model.get_particle(name).get('spin')` — if particle found, get spin+mass, break.
  - `AttributeError` (get_particle returned None → `.get` fails): if name is a multiparticle, compute `spins = set(...)` over members; **>1 distinct spin → `InvalidCmd('Can not use polarised on multi-particles for multi-particles with various spin')`** (5097). Single spin → use it.
  - elif `no_dup_name[0].isdigit()` → strip leading digit, retry (the `no_dup_name = name[1:]` duplication-count retry).
  - else `InvalidCmd('%s is not defined in the model')`.
- **`rest` non-empty** (5108): `InvalidCmd('A space is required after the "}" symbol to separate particles')`.
- Then the letter→value loop (5111-5190) populates `polarization` list. Out-of-range numeric → `InvalidCmd("polarization are between -3 and 3")`; unknown letter → `InvalidCmd('Invalid Polarization')`.

## Post-construction guard: ProcessDefinition.check_polarization (base_objects.py 3869)
Defined on the **ProcessDefinition** class (3823-4170), NOT the `Process` base class (2942-3822) — confirmed: `def  check_polarization` (double space) at 3869 sits inside ProcessDefinition. `do_add` calls it on `myprocdef` (a ProcessDefinition), so resolution is fine. Called in `do_add` at 3324 AFTER ProcessDefinition is built. Returns True (ok) / False (ambiguous). Algorithm: per final-state pid, collect polarization sets; an unpolarised occurrence registers full range `list(range(-3,4))`. Returns **False** when the same pid appears both polarised-with-a-value and unpolarised/full-range, or two overlapping polarised sets — i.e. `p p > Z{T} Z`.
- On False, `do_add` (3325) logs `logger.critical("Not Supported syntax:\n   Syntax like p p  > Z{T} Z are ambiguious...")` then `self.ask('Do you want to continue','no',['yes','no'])`. `'no'` → `InvalidCmd("Not supported syntax of type p p  > Z{T} Z")`.

## CAUTION
- check_polarization only inspects `state==True` (final-state) legs (3877 skips initial).
- The multiparticle uniform-spin check at 5097 keys on distinct *spin* values, not particle count.
