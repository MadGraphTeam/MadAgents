---
description: The leg loop in extract_process — particle-name → pdg resolution (get_copy, multiparticles, digit pdg, leading-digit duplication-count strip), the MultiLeg vs MultiTagLeg branch on LoopOption, and the MODEL-GATED case-insensitive lowercasing (5004, case_sensitive flag, import_ufo collision check) + BSM-names lesson (unknown name = hard InvalidCmd at 5242 pre-generation; take names from display particles, not PDG/paper convention; HVT/MSSM_SLHA2 examples).
---

# Particle-name resolution in the leg loop (v3.7.1)

`$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py`, leg loop **5043-5242** inside `extract_process`.

## Case-insensitivity is MODEL-GATED (5002-5004) — the lowercasing site
Before any filter peel or tokenization, `extract_process` does:
```
if not self._curr_model['case_sensitive']:
    line = line.lower()          # 5004
```
So the WHOLE process line is lowercased iff the loaded model carries `case_sensitive=False`. This is the only place a leg token is case-folded — `get_copy`/`find_name` themselves compare with exact `==` (base_objects.py 555/558, 572/574), so resolution is NOT case-insensitive at the comparison layer; the upstream line-lower is what makes `N2`→`n2` resolve.

- **Default is `case_sensitive=True`** (base_objects.py 1097). The UFO importer flips it to `False` (import_ufo.py 567) **only when lowercasing introduces no name collision** — i.e. the set of all names+antinames has the same size as the set of their lowercased forms (import_ufo.py 563-566). A model with two particles differing only by case (e.g. `X0`/`x0`) stays case-sensitive.
- **Two-sided consistency:** when `case_sensitive=False` the importer also stores the particle's `name`/`antiname` lowercased (import_ufo.py 1273-1274, `value.lower()`). So both the query line and the stored keys are lowercase — the exact `==` in `find_name` works.
- HVT and MSSM_SLHA2 both qualify (no case-only-distinct names), so for them `generate p p > N2 n1` (uppercase) resolves exactly like `n2 n1`. The load-bearing point is *identity of outcome* (uppercase result == lowercase result), not any specific count — one probe anchor for THIS topology: `N2 n1` in MSSM_SLHA2 gave `4 processes, 20 diagrams` (example only; counts are per-process, derive/probe fresh — never a recipe).
- **Trap:** case-insensitivity is NOT universal — it depends on the model. Don't tell a user "names are case-insensitive" without the `case_sensitive=False` premise; a collision-bearing model is case-SENSITIVE.

## BSM/custom-model names must come from the imported model, never guessed
An unknown name is a HARD `InvalidCmd("No particle %s in model")` at the leg loop (5242), raised inside `extract_process` (called from `do_add` 3310) **before** `check_polarization` (3324), before `diagram_generation.MultiProcess` (~3368), and before any `output` dir. No silent fallback, no fuzzy match, no PDG-convention guess — the `generate` command itself aborts and no amplitude is added.

Take BSM names from `display particles` or the model's `particles.py`, not from PDG/paper conventions. Probe-anchored misses (all → `No particle X in model`, no output dir):
- **HVT** (`models/HVT`): `zp`/`Zprime`/`zprime`/`V0`/`Vprime`/`W'` all fail. Actual heavy-vectors: `vz` (neutral, pdg 9000001), `vc+`/`vc-` (charged, 9000002).
- **MSSM_SLHA2**: `chi20`/`neutralino2`/`~chi20`/`neu2`/`ni2`/`chi10` all fail. Actual: neutralinos `n1 n2 n3 n4`, charginos `x1+ x1- x2+ x2-`.

Distinguish from a case miss: a genuinely-wrong name fails even after lowering (`zprime`≠`vz`); a right-name-wrong-case "miss" does NOT fail in these models (lowered first). If `NAME` fails but you expect it to exist, check `display particles` for the real spelling, not the letter case.

## Loop structure
- `args = self.split_arg(line)` (5043) after all filters/orders stripped.
- `myleglist = base_objects.MultiLegList()` (5045); `state=False` until `>` seen.
- `>` token (5056): if `myleglist` empty → `InvalidCmd("No final state particles")`; else `state=True`.

## Resolution precedence for each `part_name` (5192-5223)
1. **Multiparticle** (5193): if `part_name in self._multiparticles`. Tagged final-state multiparticle → `InvalidCmd("Multiparticles cannot be tagged")` (5195). Or-multiparticle (first elem is a list) → `InvalidCmd(... only for required s-channels)`. Else `mylegids.extend(self._multiparticles[part_name])`.
2. **Digit / signed digit pdg** (5201): `int(part_name) in particle_dict` → append int; else `InvalidCmd("No pdg_code %s in model")`.
3. **Name via get_copy** (5207): `self._curr_model['particles'].get_copy(part_name)` — `get_copy` (base_objects.py 526) tries `find_name` (matches name OR antiname, sets is_part), then falls back to PDG-int match. On hit append `get_pdg_code()`.
4. **Leading-digit duplication count** (5213): if name unresolved AND `part_name[0].isdigit()`, then `duplicate, part_name = int(part_name[0]), part_name[1:]` — e.g. `2j` means two copies of `j`. Retried as multiparticle or get_copy. NOTE only the FIRST char is taken as the count (single-digit multiplier).

## Leg construction (5225-5242)
- For `_ in range(duplicate)`:
  - **tree/virt/sqrvirt/noborn** `LoopOption` (5227): if `is_tagged` → `InvalidCmd("%s mode does not handle tagged particles")`. Append `base_objects.MultiLeg({'ids','state','polarization'})`.
  - **else (FKS/real/all NLO)** (5236): append `fks_tag.MultiTagLeg({'ids','state','polarization','is_tagged'})`.
- Empty `mylegids` → `InvalidCmd("No particle %s in model")` (5242).

## get_particle (base_objects.py 1303)
Used by the `{pol}` spin lookup. Tries `particle_dict[id]`; for str falls back to lazily-built `name2part`. Returns `None` on miss (the `{pol}` path catches `AttributeError` from `.get(...)` on None — see polarization-parse-step.md).

## CAUTION
- get_copy resolves antiname too; `u~` and `u` both resolve, is_part flag differs.
- Resolution order means a multiparticle name shadows a same-named particle (multiparticle checked first).
- `get_copy`/`find_name` compare with exact `==`, but the line is already lowered upstream (5004) for `case_sensitive=False` models — don't read the `==` as proof of case-sensitivity. Case behavior is decided at 5002-5004, not in `get_copy`.
