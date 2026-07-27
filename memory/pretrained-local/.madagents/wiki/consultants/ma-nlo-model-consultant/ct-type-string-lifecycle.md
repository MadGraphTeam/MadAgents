---
description: The CT interaction 'type' string is a layered tag (R2/UV family + 6-char subtype + Neps Laurent suffix) assembled by the importer and decoded layer-by-layer by the is_* predicates and diagram-gen consumers.
---

# The CT `type` string: one layered tag drives a CT vertex's whole fate

(v3.7.1, `$MADGRAPH_INSTALL`.) Deeper principle behind three instance pages
(ct-files-and-vertex-types, ct-vertex-consumers, loopmodel-detection): a CT
interaction's single `type` string is a **layered tag**, assembled in one place and
decoded everywhere else by fixed-length-prefix / substring tests. Knowing the layering
predicts behavior for cases the instance pages don't individually enumerate.

## The three layers
A classified CT interaction's final `type` is built as:
`<subtype><poleSuffix>` where the subtype carries the family in its first 2 chars.
- **Family (chars [:2])** — `R2` or `UV`.
- **Subtype (chars [:6])** — `UVmass` / `UVloop` / `UVtree` (the `UV` family only;
  `R2` has no 6-char subtype split).
- **Laurent suffix** — appended for poles: finite = none, single-pole = `1eps`,
  (double-pole is rejected). So a single-pole UVloop CT has `type=='UVloop1eps'`.

## Assembly (one place): `$MADGRAPH_INSTALL/models/import_ufo.py`
- 1568-1579: bare `UV` is guessed → `UVmass` (2 identical-name particles) else `UVloop`;
  an explicitly-declared `UVtree`/`UVloop`/`R2`/`UVmass` skips the guess. Anything not in
  `['UV','UVloop','UVtree','UVmass','R2']` → MadGraph5Error.
- 1644-1649: `add_interaction(..., intType if poleOrder==0 else intType+str(poleOrder)+'eps', ...)`.
  The suffix is concatenated onto the subtype here — that is why the suffix sits AFTER
  the 6-char subtype, leaving both prefix layers intact.

## Decoding (everywhere else): `$MADGRAPH_INSTALL/madgraph/core/base_objects.py:775-857`
Each predicate reads ONE layer by fixed-length prefix or substring:
- `is_R2`/`is_UV`: `type[:2]==` family. `[:2]` so eps-suffixed types still match.
- `is_UVmass`/`is_UVloop`/`is_UVtree`: `type[:6]==` subtype. `[:6]` (not exact-match) so
  `UVloop1eps` still satisfies `is_UVloop()`.
- `get_epsilon_order`: substring test `'1eps' in type` → 1, `'2eps' in type` → 2, else 0.

**Consequence the instance pages don't state:** one CT interaction satisfies MULTIPLE
predicates at once. `UVloop1eps` is simultaneously `is_UV()==True`, `is_UVloop()==True`,
and `get_epsilon_order()==1`. The prefix lengths are chosen precisely so the layers
decode independently. The routing consumers (set_Born_CT keys on `is_UVtree`,
set_LoopCT_vertices on `is_UVmass`/`is_UVloop`/`is_R2`) therefore route on the subtype
layer regardless of the suffix layer.

## Boundary
- Applies only to interactions assembled through `add_interaction` with a CT `type`.
  Born interactions default `type==''`, where every `is_*` returns False (the
  `len(self['type'])>=2/>=6` guards), so a Born vertex decodes to "no layer set".
- Static-string mechanism only — predicts which predicates fire, NOT runtime numerics
  (diagram counts / σ); those need a probe.
- `is_UVCT` is NOT a `type`-string layer: it reads the synthetic `'UVCT_SPECIAL'` ORDER
  key tagged during set_Born_CT, not the type string. Don't conflate it with this scheme.
