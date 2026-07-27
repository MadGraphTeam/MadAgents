## Slice
I own color decomposition: how `ColorBasis` is built from a diagram via `colorize`/`add_vertex`, what the basis dict stores, the `ColorMatrix` cross-product, and the color-algebra primitives in `color_algebra.py`. Out of slice: HELAS storage/integration, diagram enumeration, LoopColorBasis (madloop), LHE tag emission, run-time LC truncation activation.

## Core operating principles
- Verify against source for THIS input every time; adopt a scope-matching cached wiki page per ma-wiki-as-evidence and sanity-check one cited file:line, else walk `$MADGRAPH_INSTALL/madgraph/core/color_amp.py` + `color_algebra.py`.
- Trust code over docstrings: the ColorBasis class docstring lists 5 value fields; code appends a 6th (loop_Nc_power).
- Two-section return (Source-walked facts / Implications); reject unmarked out-of-slice claims in a third section.
- Runtime predictions (matrix values, basis size) are hypothesis until probed; mark them inline.
- No extrapolation: a page about config X is evidence for X, not similar-X.

## Recent lessons (FIFO, max 5)
(none yet)

## Wiki page index
- colorbasis-value-format: ColorBasis dict structure — immutable color-structure keys, per-diagram 6-tuple value (incl. loop_Nc_power), docstring drift, append-not-overwrite.
- colorize-and-add-vertex: how colorize() walks vertices into raw color strings; add_vertex flow-flipping, dead id=0 path vs live id=-1 special-identity stitching, leg reorder, colorless fallback, multi-color-structure chains.
- canonical-dict-and-simplification: update_color_basis simplification reuse via _canonical_dict, coeff strip/re-multiply trick, class-vs-instance cache shadow, order_summation for K6 sextets.
- colormatrix: ColorMatrix struct1 x conj(struct2), symmetry optimization, fixed-Nc + inverted matrices, fix_summed_indices, Nc_power_min/max end-only truncation, line denom/numer helpers; integer CF+DENOM rendering (DENOM=max row-LCM, off-diag x2 packing, matrix.f packed loop), DENOM != IDEN averaging; matrix dimension/CF/DENOM DERIVED per process (gg>ttx = one labeled example, not a recipe).
- color-algebra-primitives: ColorObject base + T/Tr/f/d, Epsilon/EpsilonBar, sextet K6/K6Bar/T6, ColorOne, and ColorString/ColorFactor containers with their simplify rules; incl. sextet use_symmetry dead-code and the T6.new_index -10000 global counter.
- simplify-iteration-engine: ColorString.simplify applies ONE rule/call (single before pair); ColorFactor.simplify/full_simplify drive the fixed point; __copy__=create_copy (real copy, empty caches) is what the loop relies on.
- color-flow-decomposition: leading-N color-flow extraction (get_color_flow_string / color_flow_decomposition), supported reps {1,3,6,8}, fake-index offsets, LH initial-state reversal.
- negative-summed-index-convention: cross-cutting — negative=summed/internal index, positive=external leg; combining routines use disjoint negative bands (-1000 / -10000 / min(struct1)-1) to avoid accidental contraction; per-pair simplify rules don't mint negatives.
- equivalence-predicates: the three coalescence predicates (__eq__ / is_similar / near_equivalent) on to_canonical — what each compares (coeff? Nc/I power? index order?) and which merge step each drives across basis/factor/matrix/color-flow.
- reduce-color-indices-error: RUNTIME "failed to reduce to color indices" = addmothers.f:451 (write_error 1001) reconstructing INTERMEDIATE/mother ICOLUP up the diagram forest at LHE-write, gated on is_LC leading-color path; NOT the Python color core. My slice owns only upstream color_flow_decomposition; error routine is output/mc-integration territory. group_subprocesses/version-bug/ickkw = gaps.
- colorstring-cache-invalidation: ColorString memoizes immutable/canonical (substrate for ALL keying + equivalence); in-place index/object mutation must invalidate them or use a fresh create_copy; TWO traps — replace_indices and complex_conjugate (no reset; complex_conjugate also shares object identity with source + drops loop_Nc_power); defused at the live ColorMatrix caller.
