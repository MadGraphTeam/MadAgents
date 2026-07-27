---
description: LoopColorBasis — closing the loop color trace (T/T6/Tr by L-cut color rep), loop_Nc_power tracking, born vs loop dict lists (loop_color_amp.py, MG5_aMC v3.7.1)
---

# Loop color basis

`$MADGRAPH_INSTALL/madgraph/loop/loop_color_amp.py`. `LoopColorBasis(color_amp.ColorBasis)` (:37) — adds loop handling to the tree color basis.

## compute_loop_nc flag (:41-46)
Constructor arg. When True, independently tracks the Nc power coming from the closed color loop (`loop_Nc_power`) — expensive (double `full_simplify`), so only used for LoopInduced+MadEvent. When False, `loop_Nc_power` set to None (:100-104) so misuse crashes loudly.

## closeColorLoop (:48-104) — sews the open L-cut into a trace
The L-cut method leaves the loop open with two L-cut color indices; this re-closes them with a delta in the rep carried by the L-cut particle (`lcut_charge` = particle color):
- `|charge|==1` (singlet): nothing to do (:57-59).
- `|charge|==3` (triplet): `T(n1,n0)` (:60-62).
- `|charge|==6` (sextet): `T6(n1,n0)` (:63-65).
- `|charge|==8` (octet): `Tr(n1,n0)` with factor 2 (:66-69).
- else: `ColorBasisError("L-cut particle has an unsupported color representation")` (:70-71).
- Negative charge reverses the index order first (:55-56).
- The closing color string is `.product()`-ed onto every color string of the diagram (:74-83).

## create_loop_color_dict_list (:106-138)
- For each loop diagram with `type>0` (true loops; R2 have negative type), gets `starting`/`finishing` loop line, looks up the L-cut particle color, and calls `closeColorLoop` (:118-128).
- UVCT diagrams colorized like ordinary diagrams, no loop closing (:133-136).
- `build_loop` / `build_born` (:160-176) call the corresponding dict-list builder then `update_color_basis`.

## Note
This is the loop-color path. Tree-level color decomposition (the `ColorBasis` mother class, `colorize`, color-flow output) is the color-decomposition slice; only `LoopColorBasis` and loop-trace closing are in this slice.
