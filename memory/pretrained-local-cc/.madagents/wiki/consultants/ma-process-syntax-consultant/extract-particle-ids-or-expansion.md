---
description: extract_particle_ids id-expansion — expand_list_list Cartesian product over |-groups, the len==1 return-shape flatten, the isinstance([0],list) discriminator for or-multiparticle position, and the probe-confirmed trap that a GLUED z|a is not split (| must be space-separated).
---

# extract_particle_ids or-multiparticle expansion (v3.7.1)

`$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py`, `def extract_particle_ids(self, args, crash_on_duplication=False)` at **5591**. Shared by `do_define` body (3555-3556) and the four filter positions in extract_process: `/` forbidden particles (5300), `$` forbidden on-shell s-channels (5307), `$$` forbidden s-channels (5309), `> >` required s-channels (5321, the only `crash_on_duplication=True` caller). The other pages *reference* this function; this one walks its id-expansion algorithm and its return-shape, which are the load-bearing, non-obvious parts.

## Build phase (5601-5618): args → all_ids (list of id-lists per |-group)
Per token (5603-5617), in this precedence:
1. `get_copy(part_name)` hit → `ids.append([pdg])` (a 1-element list).
2. multiparticle → `ids.append(self._multiparticles[part_name])` (the member-pid list).
3. token `== '|'` → **flush**: `all_ids.append(ids); ids=[]` — each `|` closes the current or-group.
4. signed digit → `ids.append([int])`.
5. else → `InvalidCmd("No particle %s in model")`.
After the loop `all_ids.append(ids)` (5618) flushes the final group. So `all_ids` is one entry per `|`-separated group, each a list of id-lists.

## Expand phase (5621-5623): expand_list_list = Cartesian product
`diagram_generation.expand_list_list` (`core/diagram_generation.py` **2167**): "Takes a list of lists and lists of lists, returns a list of flat lists. `[[1,2],[[4,5],[6,7]]] -> [[1,2,4,5],[1,2,6,7]]`." It is a **Cartesian product across groups**: a plain list contributes itself to every output; a list-of-lists contributes one branch per sublist. Each `all_ids` group is fed through `extend(expand_list_list(group))`.

## Dedup vs crash (5625-5636)
- `crash_on_duplication=False` (default, all filters except `> >`): per result list, dedup-in-place keeping order via `set_dict.setdefault`.
- `crash_on_duplication=True` (`> >` required-s-channels only): same dedup but if it shortened the list → `InvalidCmd('Particle can not be duplicate')`. This is what the leg-loop catches at 5322 and re-raises as the `Invalid "> A A >" syntax...` message.

## Return-shape flatten (5638-5639) — the discriminator
```
if len(res_lists) == 1:
    res_lists = res_lists[0]
```
A SINGLE result list is **unwrapped** from list-of-lists to a flat id-list. Multiple results (an actual or-multiparticle, ≥2 branches) stay nested. This return-shape IS the signal the leg loop tests:
- Filter positions (5301/5310/5314): `if forbidden_*_ids and isinstance(forbidden_*_ids[0], list)` → still nested → it's an or-multiparticle → `InvalidCmd("Multiparticle %s is or-multiparticle which can be used only for required s-channels")`. Or-multiparticles are legal ONLY for `> >`.
- Required-s-channel (5325-5327): the INVERSE — `if required_schannel_ids and not isinstance(required_schannel_ids[0], list): required_schannel_ids = [required_schannel_ids]` — re-wraps a flat (single-alternative) result so the downstream sees a uniform list-of-alternatives.

So `isinstance(result[0], list)` is the whole or-multiparticle detector, and the `len==1` flatten at 5638 is what makes a *single* required s-channel come back flat (needing the 5327 re-wrap) while a real `z | a` comes back nested.

## Probe-confirmed (v3.7.1, sm)
- `e+ e- > z | a > mu+ mu-` (spaced `|`) → OK, `required_s_channels = [[23],[22]]` — the or-multiparticle expands to two required-s-channel alternatives (Z OR photon). This is the `expand_list_list` output, two branches, NOT re-wrapped.
- `e+ e- > mu+ mu- $ z | a` (spaced `|` in a forbidden `$` position) → `InvalidCmd: Multiparticle mu- is or-multiparticle which can be used only for required s-channels`.

### TRAP: `|` must be SPACE-SEPARATED; glued `z|a` is NOT split
Probe-confirmed deterministic divergence:
- `e+ e- > z|a > mu+ mu-` (glued) → `InvalidCmd: Invalid "> A A >" syntax...` (the duplicate-s-channel error), NOT an or-multiparticle.
- `e+ e- > mu+ mu- $ z|a` (glued) → `InvalidCmd: No particle z|a in model`.

Traced cause (monkeypatched `extract_particle_ids`): the required/forbidden block reaching `extract_particle_ids` is the GLUED string `' z|a '` for glued input but `' z | a '` for spaced input. Isolated with a single-arrow `$` line (no `> >` peel), so the `> >` rebuild is NOT the culprit — the spacing loss is at the `/`/`$`/`> >` **filter-peel** stage (5006-5041): those regexes extract the filter substring and the glued `|` inside it survives un-spaced, even though the `space_before` regex at 4836 splits a glued `z|a` correctly in isolation. Net user-facing rule: **write `z | a`, not `z|a`** — only the spaced form is parsed as an or-multiparticle. (Exact interior peel that drops the spacing is not yet pinned; flagged as an open mechanism question, not asserted.)

### Message-naming quirk
The or-multiparticle-in-forbidden-position error interpolates `part_name` (5304), which holds whatever the **leg loop** left it at — the LAST leg name (`mu-` in the probe), NOT the offending `z|a`. So the message names the wrong particle. Cosmetic, but misleading when debugging.

## optimize_order early-returns (5648-5651)
`optimize_order(pdg_list)` (5643) — called by `do_define` (3559) on the final multiparticle list. Two no-op guards FIRST: empty `pdg_list` → return; `not isinstance(pdg_list[0], int)` → return (so a list-of-lists, i.e. an or-multiparticle, is left UNSORTED). Then four stacked stable `.sort()`s — last sort dominates: (1) `i<0` last, (2) `is_fermion()`, (3) `color` desc, (4) `mass!='zero'`. Because Python sort is stable and applied in sequence, the FINAL key (mass) is the primary grouping and pdg-sign is the weakest — groups similar species adjacently for diagram-symmetry efficiency.
