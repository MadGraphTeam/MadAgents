---
description: find_color_links/legs_to_color_link_string/insert_color_links — color(charge)-correlated born ME generation and the need_color/charge_links flag.
---

# Color-link generation for color-correlated borns

FKS soft subtraction needs color-correlated born matrix elements
B_{ij} = <M| T_i·T_j |M>. These three functions build them.

## find_color_links (fks_common.py:622)
Enumerates all (leg1,leg2) pairs of the born. `pert='QCD'`→ key `'color'`,
zero-value 1; `pert='QED'`→ key `'charge'`, zero-value 0.0 (`:628-635`). A pair is
kept if both legs are colored/charged (`!= zero`) and either different legs or
the same leg is massive (`leg1 != leg2 or not leg1['massless']`, `:640-641`) —
the diagonal self-link survives only for massive colored particles. With
`symm=True` only `leg1['number'] <= leg2['number']` pairs are produced (`:642`);
this is what `set_color_links` uses.

## legs_to_color_link_string (fks_common.py:652)
Builds the ColorString insertion for the pair. QCD off-diagonal (`:670-688`):
- color 3 (triplet, with `icol=-1` for initial state): `T(iglu,num,min_index)`,
  coeff ×(-1).
- color -3 (anti-triplet): `T(iglu,min_index,num)`.
- color 8 (octet): `f(min_index,iglu,num)`, imaginary.

QCD diagonal (leg1==leg2, massive, `:690-709`): doubled T or doubled f, coeff
× 1/2.

QED (`:711-715`): coeff multiplied by the leg charge as a Fraction; no index
algebra (charges are c-numbers). `iglu = min_index*2`, `min_index=-3000` give the
auxiliary gluon/index labels.

## insert_color_links (fks_common.py:571)
For each link, copies the original color basis `col_obj`, applies the index
`replacements`, products in the link `string`, builds a `ColorBasis` and a
`ColorMatrix(orig_basis, link_basis)`. Returns dicts with
`link`/`link_basis`/`link_matrix`/`orig_basis`.

## Where it is driven
`FKSHelasProcess.set_color_links` (fks_helas_objects.py:767) calls
`find_color_links(..., symm=True, pert=self.perturbation)` then
`insert_color_links` against the born color basis. Lazy: only if
`self.color_links` is empty.

## need_color_links / need_charge_links flag (fks_base.py:416-423)
Set per real on the i-leg: `need_color_links` true iff i is massless, spin==3,
self-conjugate, color==8 (a gluon); `need_charge_links` same but color==1 (a
photon). These tell the exporter whether to emit color- vs charge-correlated borns
for that configuration.

## Cautions
- The diagonal link exists ONLY for massive colored/charged legs (e.g. top); for
  massless legs T_i·T_i is absorbed elsewhere. Do not expect a self-link for a
  massless quark.
- QED links carry no index replacements; the "color matrix" for QED is just the
  charge-weighted born — don't look for f/T structure there.
