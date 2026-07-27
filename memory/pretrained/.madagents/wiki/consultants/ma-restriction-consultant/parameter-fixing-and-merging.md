---
description: detect_special_parameters / fix_parameter_values / detect_identical_parameters / merge_iden_parameters — zero/one external→internal conversion and identical-param merging (import_ufo.py v3.7.1)
---

# Parameter fixing and merging

## detect_special_parameters (2615)
Scans `self['parameter_dict']`. `value == 0 and name != 'ZERO'` → null list; `value == 1` → one list.
Running-model check (2628-2640): `running_param = self.get_running()` (not a direct `running.py` test — inherited accessor; empty/falsey for non-running models, which short-circuits the check). For each restricted (0/1) param, every running block it appears in is rebuilt with the `'mdl_%s'` prefix (2633), then: if ANY other member of that block is NOT also in the restricted set → `raise Exception("Model restriction not compatible with the running of some parameters. \n %s is restricted to zero/one but mix with %s which is/are not.")` naming the offending param and the unrestricted partners (2637-2638). So a running block must be restricted all-or-nothing; partial restriction of a running multiplet aborts the load.

## fix_parameter_values (2980)
- Masses/widths first (2987-3001): particle whose `mass`/`width` is a zero param → set to `'ZERO'`. A mass/width that is a ONE param is removed from one_parameters (masses/widths are not forced to 1 — they keep their value). Applied over both `self['particles']` and `self['particle_dict']`.
- Rule accumulation (3005-3012): for each external param, value 0 → `rule_card.add_zero`, value 1 → `rule_card.add_one`.
- `simplify=True` (default, = `rm_parameter`): regex-scan all coupling exprs and lorentz form-factors for occurrences of the special params; only those still USED are kept (recreated as internal `ModelVariable` with expr `'0.0'`/`'1.0'`, 3085-3088). Unused ones are removed entirely (3090-3099). `simplify=False` keeps all special params as 0.0/1.0 internals.
- `keep_external=True`: external special params are NOT removed even if unused (3093-3096).
- Big-regex guard: re_str split in half if > 25000 chars ("size limit on mac", 3021).

## detect_identical_parameters (2709)
Only EXTERNAL params. Skips values in `[0,1,0.000001e-99,9.999999e-1]` (2724) and skips `decay` block (2726). Groups by `(lhablock, value)`; opposite value (`-value`) grouped with coeff -1. Returns groups with >1 member.

## merge_iden_parameters (2825)
- First member kept; others get a param_card RULE: coeff 1 → `add_identical`, coeff -1 → `add_opposite` (2843-2848).
- Non-kept member removed from external list unless keep_external (then only MASS/DECAY removed; others have name blanked, 2851-2857).
- New internal `ModelVariable(name, 'factor*expr', 'real')` inserted (2859-2860).
- MASS/DECAY merges also rewrite particle mass/width fields to the kept name (2864-2874) — enables multi-process optimisation. GUARD (2872-2874): the particle `mass`/`width` field is rewritten ONLY for members merged with `factor==1` (identical); an opposite-value (`factor==-1`) member's particle field is NOT repointed (`factor_for_name[...]==1` filter at 2873-2874). The `add_opposite` rule still records the negation for card-check, but the particle keeps its own mass/width name.

## Subprocess-grouping enabler (restriction's contribution, not the grouping itself)
Grouping massless quarks (u,d,s,c) into one subprocess keys on identical matrix elements — which requires identical masses AND identical (here: absent) couplings. Restriction's role for the SM is narrow and specific:
- In the SM UFO, u/d/s already carry `mass = Param.ZERO` (particles.py — hardcoded massless, NOT a restriction effect); only charm carries `mass = Param.MC` (external).
- `restrict_default` sets `MC=0`. `fix_parameter_values` (2987-2992) then sees charm's mass param MC ∈ zero_parameters → rewrites charm's particle `mass` field to the literal `'ZERO'`. Now u,d,s,c ALL share the single `'ZERO'` mass identifier — the precondition for treating them interchangeably.
- The zero charm Yukawa additionally prunes the c-c-H/G0 vertices (removed-coupling-not-small.md), so charm carries no coupling that distinguishes it from u/d/s.
- For non-mass identical externals, `merge_iden_parameters` (2864-2874) repoints particle mass/width fields to one shared name — same "shared identifier" mechanism, general case.
So restriction supplies the SHARED-mass-identifier + absent-Yukawa precondition. The actual subprocess grouping (`group_subprocess.py`, and multiparticle `p`/`j` membership) is diagram-generation / model-loader territory, NOT restriction.

## Caution
`merge_iden_parameters` is called in TWO passes (pipeline steps at 2444-2452): first without keep_external (guarded by `if not keep_external`), then with keep_external. Masses and widths are always removed on merge regardless of keep_external.
