---
description: amp_split + orderstag machinery — write_orders_file/orders.inc (nsplitorders, qcd_pos/qed_pos, amp_split_size), get_orderstag base-N encoding, sborn_sf_fks amp_split_soft, HAS_AN_HEFT_VERTEX; BSM ride-through (NP/many-order split_orders chunked ordernames, qcd_pos/qed_pos=-1 guarded by runtime need_*_links, missing-order sentinel in else-branch, orders_to_amp_split_pos bodies helas-owned).
---

# amp_split / orderstag coupling-power accounting (v3.7.1)

Tracks the different coupling-power combinations entering each ME so NLO mixed-coupling expansions can be split (QCD/QED powers).

## get_orderstag (export_fks.py:66)
`orderstag_base` module constant set at `:64`; `get_orderstag(ords)` (`:66`) encodes an order tuple as a single integer in base `orderstag_base` (`tag = sum(o_i * base^i)`), so each order count must be < that base. Read the literal base at `:64`. Used by `write_orderstag_file` (`:1143`) to write `SubProcesses/orderstags_glob.dat` (one tag per splitorder combo) — called from `amcatnlo_interface.py:1011`, not from the exporter's own dir loop. `orderstag_base.inc` (`write_orderstag_base_file` `:1150`) emits `parameter (orders_tag_base=<base>)` (value read at `:64`/`:1150`); written in `finalize` (`:889`).

## write_orders_file (export_fks.py:1239) → orders.inc
The central accounting routine. Returns `(amp_split_orders, amp_split_size, amp_split_size_born)`. Called from `generate_directories_fks` (`:634`, via `FortranWriter90`) and EW-Sudakov `generate_directories_fks` (`:5187`, via plain `FortranWriter`). NOT from `generate_born_fks_files` — that method (`:2140`) writes only the `born_*` files / color-links / EW-Sudakov MEs; orders.inc and the linkfiles/amp_split_orders block are written by `generate_directories_fks` AFTER the born-files call returns (`:502`). (Corrected pass-3: prior page said `generate_born_fks_files :633`.)

Builds, from `matrix_element.born_me['processes'][0]`:
- `split_orders` = the `'split_orders'` list (e.g. ['QCD','QED']).
- `max_born_orders` / `max_nlo_orders`: if user gave only WEIGHTED, derived from per-combo weighted-hierarchy filtering (`:1264`); else taken from `born_sq_orders`/`squared_orders`, defaulting missing orders to the missing-order sentinel (`:1294`/`:1299`, read the literal there).
- `qcd_pos` / `qed_pos`: 1-based index of QCD/QED in `split_orders`, or **-1** if absent (`:1303`–`:1308`).
- `amp_split_orders`: union of born `get_split_orders_mapping()` squared_orders (first `amp_split_size_born` entries, `:1319`), then real-emission squared_orders (`:1323`), then virtual squared_orders (`:1334`, AttributeError-guarded for no-virt). For ewsudakov, appends born_orders with QED+2 (`:1348`).
- `amp_split_size = len(amp_split_orders)`.

orders.inc emitted text (`:1361`+): `nsplitorders` param, `ordernames` array (split into fixed-size chunks past an order-count threshold, `:1366`, read the threshold/chunk size there), `born_orders`/`nlo_orders` data, `qcd_pos`/`qed_pos` params, `amp_split_size`/`amp_split_size_born` params, and the arrays:
```
double precision amp_split(amp_split_size)
double complex amp_split_cnt(amp_split_size,2,nsplitorders)
common /to_amp_split/amp_split, amp_split_cnt
```

## amp_split PRODUCER side (bornmatrix_splitorders_fks.inc — and real/cnt siblings)
orders.inc only DECLARES the arrays; the split-order ME templates (`bornmatrix_splitorders_fks.inc`, `realmatrix_*`, `born_cnt_*`) FILL them. Mechanism (bornmatrix template):
- Reset: `amp_split(1:amp_split_size)=0d0`; `amp_split_cnt(1:amp_split_size,1:2,1:nsplitorders)=dcmplx(0d0,0d0)` (`:131`-132). Confirms `amp_split_cnt` dims = (size, 2, nsplitorders).
- Per squared-split-order combo `i`: `amp_orders(j)=GETORDPOWFROMINDEX_B(j,i)` (the coupling powers of combo `i`), then `amp_split(orders_to_amp_split_pos(amp_orders)) = ans(1,i)` (`:141`-144) — maps each computed squared-order value into its amp_split slot, gated on `abs(ans)>max_val*tiny`.
- `amp_split_cnt(pos,1,j) = ans(1,I)` and `amp_split_cnt(pos,2,j) = ans(2,I)` (`:180`-181): the 2nd dim {1,2} is the two pieces (real / second interference slot) per split-order `j`. THIS is the producer of the values `sborn_sf_fks.inc` later reads as `amp_split_cnt(:,1,qcd_pos)`.
- Coupling-power filtering: combos with `GETORDPOWFROMINDEX_B(j,i) > born_orders(j)` (or `> nlo_orders(k)-ord_subtract`) are skipped (`:72`-89) — born_orders/nlo_orders from orders.inc are the per-order ceilings.
- EW-Sudakov block (`:243`+): fills `amp_split_ewsud`/`amp_split_ewsud_LO2` with `/iden` averaging (`iden=iden_values(nfksprocess)`, `:268`).
So: write_orders_file declares + sizes (Python side); GETORDPOWFROMINDEX/orders_to_amp_split_pos + these templates populate (Fortran runtime); sborn_sf consumes. orderstag is the integer key the Python side used to dedup/index the combos.

## amp_split_orders.inc (write_amp_split_orders_file :1132)
`integer amp_split_orders(N, nsplitorders)` + DATA lines mapping each amp_split index to its order tuple. orders.h (`:1175`) emits C `#define __amp_split_size` / `__amp_split_size_born` for amcblast.

## BSM split-order ride-through (NP / many orders / QCD-or-QED absent)
`split_orders` is whatever the matrix element carries — NOT hardcoded to ['QCD','QED']. For a BSM/SMEFT-at-NLO process it includes NP (and any model-specific order) too. Source-confirmed propagation (`:1359`-1402):
- `nsplitorders = len(split_orders)` and `ordernames` array carry ALL orders verbatim (`:1363`/`:1365`). Past an order-count threshold the ordernames DATA is emitted in fixed-size chunks via an `ORDERNAMEINDEX` loop (`:1366`-1378, read the threshold/chunk size there) so the linked-from-both-f77/f90 file stays within line length. A many-order BSM model is the case that trips into this chunked path.
- `born_orders`/`nlo_orders` DATA arrays are emitted ordered by `split_orders` for EVERY order (`:1382`-1383), with the per-order ceiling = the explicit `born_sq_orders`/`squared_orders` value, or the **missing-order sentinel** for any split order ABSENT from that explicit per-order dict. CRITICAL — the sentinel fill lives in the **`else` branch** (`:1288`-1299, read the literal there), i.e. the path taken when `born_orders.keys() != ['WEIGHTED']`; a `KeyError` on a missing order → sentinel (`:1294`/`:1299`). It is NOT the WEIGHTED-only branch: when the user constrains ONLY WEIGHTED, the `:1264` weighted-hierarchy branch runs instead and `max_nlo_orders` is never even populated (no sentinel assigned there). So NP=sentinel happens when the user gave explicit per-order constraints (e.g. on QCD/QED) but left NP out of `born_sq_orders` — not "when the user constrained only WEIGHTED".
- `amp_split_orders` (and hence `amp_split_size`) is the union of born+real+virt squared-order TUPLES — each tuple has one slot per split order including NP. So adding an NP power as a new combo grows `amp_split_size`, not `nsplitorders`. The amp_split / amp_split_cnt arrays are sized by these BSM combos automatically.
- `qcd_pos`/`qed_pos` are JUST the 1-based index of 'QCD'/'QED' in `split_orders`, or **-1** if absent (`:1305`-1308). A pure-EW or pure-NP BSM born can legitimately have `qcd_pos = -1`; a process with no QED order has `qed_pos = -1`. These are emitted as bare `parameter` values (`:1387`-1388, `parameter (qcd_pos = %d)` / `parameter (qed_pos = %d)`) — nothing in orders.inc guards the -1.

## qcd_pos/qed_pos = -1 robustness — guarded by runtime need_*_links, NOT by orders.inc (sborn_sf_fks.inc, full template)
The -1 sentinel would be an out-of-bounds Fortran index if dereferenced. It is NOT, because `sborn_sf` selects the branch by RUNTIME flags from `/c_need_links/` (`need_color_links`, `need_charge_links`), and a process raises/stops if both are set:
```
if (need_color_links.and.need_charge_links) then ... stop   ! sborn_sf_fks.inc:31-34
if (need_color_links) then  ... amp_split_soft = dble(amp_split_cnt(:,1,qcd_pos))*g**2   ! :36-40
else if (need_charge_links) then ... amp_split_soft = dble(amp_split_cnt(:,1,qed_pos))*chargeprod*gal(1)**2   ! :42-49
```
So `qcd_pos` is dereferenced ONLY when a color link is actually requested at runtime (which FKS only does when QCD is a split order, i.e. qcd_pos≠-1); `qed_pos` only inside the charge-link branch. The protection is the FKS subtraction's link-type choice, not a compile-time check. Consequence for a BSM process: if it has color links it must have QCD in split_orders (qcd_pos≥1); a pure-NP-corrected color-singlet process takes the charge-link branch and needs qed_pos≥1.

## b_sf_xxx_splitorders_fks.inc — color-link producer, QCD power +2
The color-link soft-correlated born ME template (`b_sf_NNN.f` per `matrix_element.color_links`) is the PRODUCER of `amp_split_cnt(:,1,qcd_pos)` that sborn_sf consumes. It bumps the QCD amp_order by 2 before mapping (`b_sf_xxx_splitorders_fks.inc:62`: `if (j.eq.qcd_pos) amp_orders(j) = amp_orders(j) + 2`), then `amp_split_cnt(orders_to_amp_split_pos(amp_orders),1,qcd_pos)=ans(i)` (`:65`) — the +2 is the soft g**2 factor's coupling power, gated on `keep_order_cnt(qcd_pos,i)`.

## Boundary: orders_to_amp_split_pos / GETORDPOWFROMINDEX bodies are NOT mine
The FKS split-order ME templates (bornmatrix/realmatrix/born_hel/born_cnt/b_sf splitorders_fks.inc) CALL `orders_to_amp_split_pos(...)` and `GETORDPOWFROMINDEX_B(...)` but their Fortran BODIES are generated by the helas/output side (helas_objects split-order machinery via the LO ME writer), not by export_fks — the only export_fks mention is the `:1313`-1314 comment naming `orders_to_amp_split_pos.inc`/`amp_split_pos_to_orders.inc` as where they live. My slice owns the FKS templates that consume the mapping; the mapping-function generation is output/helas territory.

## sborn_sf_fks.inc — amp_split_soft
`template_files/sborn_sf_fks.inc` defines `subroutine sborn_sf` for soft FKS born color/charge correlations. Declares:
```
double precision amp_split_soft(amp_split_size)
common /to_amp_split_soft/amp_split_soft
```
Color-link branch: `amp_split_soft = dble(amp_split_cnt(1:amp_split_size,1,qcd_pos)) * g**2`.
Charge-link branch: `amp_split_soft = dble(amp_split_cnt(1:,1,qed_pos)) * chargeprod * dble(gal(1))**2`.
So `qcd_pos`/`qed_pos` from orders.inc directly index the third dim of `amp_split_cnt` for the soft correlated born.

## HAS_AN_HEFT_VERTEX (loop_optimized/TIR_interface.inc, written by write_TIR_interface loop_exporters.py:2219)
`LOGICAL HAS_AN_HEFT_VERTEX(NLOOPGROUPS)` (TIR_interface.inc:475). Per loop-group flag: True if a loop wavefunction vertex is built from only massless vectors + massive scalars (≥1 each) — the HEFT ggH vertex signature (`:2240`). Passed to `DETECT_LOOPLIB` (`:514`,`:531`) to honour CutTools' limitation on such vertices, influencing reduction-library selection at runtime.

## Cautions
- the base-N orderstag breaks silently if any single order count reaches `orderstag_base` (`:64`, read the literal) — no guard in get_orderstag.
- Missing orders default to the missing-order sentinel in max_born/nlo_orders (`:1294`, read the literal) — a sentinel, not a real bound; downstream Fortran treats it as "unconstrained".
- `amp_split_size` is union over born+real+virt, so it can exceed `amp_split_size_born`; the first `amp_split_size_born` entries are the born combos (assumed ordering in sborn_sf and elsewhere).
