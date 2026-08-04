---
description: ALOHA's symbolic-optimization engine (aloha_lib.py simplify/expand/factorize/split) — the polynomial-algebra layer the high-kernel tail drives to turn a contracted tensor into the optimized Fortran body. Distinct from the __mul__ tensor-contraction engine (lorentz-primitives.md).
---

# Symbolic-optimization engine (aloha_lib.py)

Cites `$MADGRAPH_INSTALL/aloha/aloha_lib.py` and `create_aloha.py`, v3.7.1. lorentz-primitives.md documents the TENSOR-CONTRACTION engine (`LorentzObjectRepresentation.__mul__`/`contraction`, the Einstein-sum that evaluates a contracted expression). THIS page is the POLYNOMIAL-ALGEBRA layer above it: how the flat sum-of-products that contraction yields is collected, expanded, factorized, and (for loops) split into rank-graded coefficients. These are the methods the high-kernel tail actually calls.

## The pipeline the high-kernel tail drives
`compute_aloha_high_kernel` tail (`create_aloha.py:415-425`):
```
lorentz = lorentz.simplify()           # collect like terms
if loop tag: return compute_loop_coefficient(...)   # split path, below
lorentz = lorentz.expand()             # High-level objects -> low-level Variable products
lorentz = lorentz.simplify()           # collect again post-expand
if factorize: lorentz = lorentz.factorize()   # greedy common-factor extraction
```
Loop tail `compute_loop_coefficient` (`:628-634`): `expand(veto=veto_ids) -> simplify -> split(veto_ids) -> per-coeff simplify().factorize()`.

So the body of an emitted routine is the OUTPUT of `factorize` (or, for loops, of per-coefficient `factorize`). The nested `COUP*(...)` / `(maxvar * (...))` shape in a generated `*.f` is this engine's product, not the contraction engine's.

## simplify — like-term collection (`AddVariable.simplify` `:212`)
Collects terms of an `AddVariable` (the `+` node) by canonical sort-tag (`term.sort()`, `:232`), summing prefactors of identical monomials (`:233-240`). Notable:
- **Float-cancellation guard** (`:236-238`): if a summed prefactor shrinks below a small relative threshold (read the literal at `aloha_lib.py:237`) of the magnitudes that produced it, it is forced to 0 (kills `0.33333 - 0.3333` residue). This is a numerical-cancellation rule baked into the SYMBOLIC layer — a near-cancelling term is dropped, not kept.
- Pulls a common scalar prefactor out of the whole sum (`countprefact`/`fact_prefactor`, `:246-280`): the most-frequent absolute prefactor is factored to `self.prefactor`, and the sign is flipped to make the majority of terms positive (`nbplus<nbminus → *-1`, `:271-272`).
- Returns a bare number / single term when the sum collapses to length 1 or 0 (`:285-294`).
`MultVariable.simplify` (`:665`) is trivial — a product only collapses to its prefactor when empty.

## expand — High→low + smart contraction ordering (`MultLorentz.expand` `:946`)
`expand` turns High-level Lorentz objects into low-level `Variable` products (the form `simplify`/`factorize` operate on). `MultLorentz.expand` (`:946`) is the contraction-ORDERING engine:
- Seeds chains from `contract_first` objects (`:955`) — P/S/fermion primitives carry `contract_first=1` (e.g. `L_P`, lorentz-primitives.md), so contraction starts from momenta/spinors to MINIMIZE uncontracted indices during the walk.
- Greedily extends each chain to a contracted `neighboor` (`:981-985`).
- **`veto`** (docstring `:949-951`; operative check `:1000` `if not veto or not scalar.contains(veto)`): forbids contracting a scalar sub-expression that contains any vetoed variable id. In the loop path the loop-momentum component ids (`PL_0..3`, set at `create_aloha.py:621`) plus the open-loop wavefunction components are vetoed, so loop-momentum factors stay UN-contracted/standalone — that is what lets `split` peel them off as the rank grading.
`AddVariable.expand` (`:340`) just distributes expand over the sum's terms.

## factorize — greedy common-factor extraction (`AddVariable.factorize` `:538`)
Recursive greedy factorization producing the nested `MultContainer` body:
- `count_term` (`:489`) counts how many terms each variable appears in. Picks the MOST-frequent variable `maxvar` (`:512-514`). Ties broken by a **correlation-weight heuristic** (`:523-528`): `wgt = sum(co-occurrence^2)/n` — prefer the variable that co-occurs with a tight cluster; remaining ties broken by LOWEST string representation (`:530-535`, deterministic).
- If `max<=1` no factorization possible, return as-is (`:550-552`).
- Else split each term into `maxvar * remainder` vs `constant` (no `maxvar`) (`:558-567`), RECURSE `factorize` on the `newadd` remainder (`:577`) and on the `constant` group (`:603-604`), and assemble `MultContainer([maxvar, newadd])` (+ constant) (`:608-616`).
- Re-optimizes the inner prefactor and majority-sign exactly as `simplify` does (`:582-600`).
`MultContainer` (vartype 6, `:618`) is the factored `(maxvar * remainder)` node; its own `factorize` (`:634`) just factorizes each member. `MultVariable.factorize` (`:819`) is the recursion base case — a product is already irreducible, so it just `return self` (no-op).

## split — rank-graded loop coefficients (`split` `:297`/`:671`)
`split(variables_id)` returns a dict keyed by the POWER each vetoed variable carries, value = the remaining product:
- `MultVariable.split` (`:671`): `key = tuple(self.count(i) for i in variables_id)` — the power-tuple of the vetoed loop-momentum/wavefunction ids; strips them from the product; returns `SplitCoefficient([(key, self)])` (`:676-679`).
- `AddVariable.split` (`:297`): merges the per-term `split` dicts, accumulating into `out[key]` (`:302-306`).
- `SplitCoefficient(dict)` (`:1514`): `get_max_rank` (`:1520`) = `max(max(key[:4]))` — reads the FIRST FOUR key entries (the loop-momentum components `PL_0..3`) and takes the max as the loop polynomial RANK. This rank feeds `q_polynomial.get_number_of_coefs_for_rank` in the loop writer (writer-lowering-mechanics.md COEFF 3D-array). The coef-count formula is `sum_{ri=0..r} (3+ri)(2+ri)(1+ri)/6` (`madgraph/various/q_polynomial.py:11-15`) — cumulative count of symmetric-tensor coefficients up to rank r (a borderline helper the writer imports; rank-counting only).

## Why this matters / cautions
- The emitted body's STRUCTURE (which factor is pulled outermost, how deep the nesting) is decided HERE by a greedy heuristic, not by the physics — so two algebraically-equal kernels can emit differently-shaped Fortran. The factorization is deterministic (string tie-break) but not "canonical" in any physics sense.
- The float-cancellation guard in `simplify` (`aloha_lib.py:237`, a small relative threshold — read the literal) means a term that nearly cancels is DROPPED at the symbolic stage — a source-visible place where a contribution can silently vanish. A pointer, not a runtime claim: if a routine seems to be missing a term you expected, this guard (or a `factorize=False` call) is a candidate.
- `factorize` is gated by the `factorize` arg to `compute_routine`/`compute_aloha_high_kernel` (default True, `create_aloha.py:159,269`). A `factorize=False` routine emits the flat expanded sum.
- This is a STATIC code-flow fact (which methods run, what they compute). The exact emitted nesting in a `<PROC_DIR>/Source/DHELAS/*.f` is a runtime instantiation — see static-codeflow-vs-runtime-artifact.md; probe to assert a specific generated line.
