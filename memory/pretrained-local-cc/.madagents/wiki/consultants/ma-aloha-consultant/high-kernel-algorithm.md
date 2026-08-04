---
description: compute_aloha_high_kernel — the core ALOHA algorithm turning a parsed Lorentz expr + spins + outgoing leg into the off-shell/amplitude expression (wavefns, propagator, simplify/expand/factorize).
---

# High-kernel algorithm (create_aloha.py:269 compute_aloha_high_kernel)

Cites `$MADGRAPH_INSTALL/aloha/create_aloha.py` v3.7.1. This is the heart of routine generation.

## Inputs / kernel caching
- `mode` = `self.outgoing` = position of the off-shell leg (1-based); `0` = all-incoming amplitude (`compute_routine` `:159`).
- Kernel = parsed Lorentz structure. First call: `parse_expression()` (`:289`) → string → `eval` into primitive-object algebra; cached in `self.routine_kernel` (`:290`) with `self.kernel_tag` (`:300`). Reuse path re-evals string or `copy.copy`s the object (`:301-306`), restoring `aloha_lib.KERNEL.use_tag`.
- Conjugate-leg flip: if `(outgoing+1)//2 in self.conjg`, swap parity of `outgoing` (`:277-279`).

## Per-leg multiplication (`:307-408`)
For each spin (id=i+1):
- **Outgoing leg (id==outgoing)** → multiply by the PROPAGATOR numerator, set `denominator`:
  - propagator tag `propa` = `[t[1:] for t in tag if startswith 'P']` (`:313`).
  - `P0` → massless branch; spin-3 + `unitary_gauge==2` uses custom `1PS` phase-space propagator (`:314-317`).
  - `[]`/`['1D']` → massive standard, `denominator=None` (1D = BW-cutoff multiplier handled separately `:380`).
  - else → custom propagator via `get_custom_propa` (`:325-331`).
  - Standard numerators by spin: scalar `*i` (`:335`); fermion (spin 2) `SpinorPropagatorout/in` w/ parity → incoming/outgoing convention (`:337-346`); vector (spin 3) `VectorPropagatorMassless` if massless or `unitary_gauge in [0,3]` else `VectorPropagator` (`:347-351`); spin-3/2 (spin 4) four Spin3half variants by mass×parity (`:352-366`); spin-2 (spin 5) `Spin2masslessPropagator`/`Spin2Propagator` (`:368-375`). Unknown spin → `AbstractALOHAError` (`:376`).
- **Incoming leg** → multiply by the WAVEFUNCTION: `Scalar` (`:386`), `Spinor(spin_id,id)` (`:393`), `Vector(id,id)` (`:395`), `Spin3Half` (`:403`), `Spin2(...)` (`:405`). Conjugate legs shift `spin_id` by `_conjugate_gap` (`:389`,`:398`).

## Tail (`:410-428`)
- No off-shell leg (amplitude, outgoing==0): `lorentz *= complex(0,-1)` (`:412`); propagators omitted.
- `lorentz.simplify()` (`:415`).
- If any tag starts with `L` (loop / OpenLoops-Pozzorini): return `compute_loop_coefficient(lorentz, outgoing)` (`:418-419`, `:593`) — emits a `SplitCoefficient` (loop writer path).
- Else `expand()` → `simplify()` → optional `factorize()` (`:421-425`); attach `lorentz.tag` from `KERNEL.use_tag`.

## Loop-coefficient tail — compute_loop_coefficient (`:593`)
When a tag starts with `L` (OpenLoops/Pozzorini open-loop leg), the tail returns a `SplitCoefficient` instead of a flat expr. Algorithm (cited `create_aloha.py` v3.7.1):
- `l_in` = the `L<n>` incoming open-loop leg (`:596`); flipped if conjugate (`:597-599`). Asserts `l_in != outgoing` (`:600`).
- Momentum shift: every `_P` momentum on leg `l_in` or `outgoing` is replaced `P_i -> P_L + P_i` (sign +1 on `l_in`) and `P_o -> -(P_L + P_o)` (sign -1 on outgoing) (`:602-618`) — re-expresses the loop momentum flowing through the vertex relative to the cut leg `L`.
- Veto set: the loop-momentum components `PL_0..3` plus the off-shell `l_in` wavefunction components (size from `WriteALOHA.type_to_size[spin]-1`, `:622-624`) are vetoed (`:621-626`).
- `lorentz.expand(veto=...)` then `.simplify()`, then `coeff_expr = lorentz.split(veto_ids)` (`:628-630`) — `split` partitions the polynomial into a dict keyed by the vetoed (loop-momentum / wavefunction) monomials → each value is the coefficient. Each coefficient is `simplify().factorize()`d (`:632-634`), and `coeff_expr.tag` records used tags (`:635`). This dict-of-coefficients is what the loop writer (`ALOHAWriterForFortranLoop`) emits as the rank-graded numerator coefficients.

## define_routine_kernel (`:644`) — first-eval path
`define_routine_kernel` (`:644`) builds the raw kernel from `self.lorentz_expr` via `eval` (`:650`); a pure-number Lorentz short-circuits and is stored as-is (`:652-654`). Otherwise `simplify()→expand()→simplify()` before caching in `self.routine_kernel` (`:655-659`). This is the kernel that `compute_aloha_high_kernel` reuses across the per-outgoing routines.

## Why this matters
The algorithm fuses wavefunction insertion + propagator numerator into a single symbolic expression, then the writer lowers it to target code. The kernel branches on `unitary_gauge` (numerator choice: axial `1PS` `:315`, massless vector `:348`) and the loop tail (`:418`); mass enters only as the `massless` flag steering the numerator. It does NOT branch on `complex_mass` at all, and `unitary_gauge==3`/`loop_mode` also branch heavily in the WRITER (target lowering: layout, declarations, precision, CMS emission). So "everything branches in the kernel" is false — see propagators-and-gauge-flags.md for the kernel-vs-writer flag-routing split. Tags (`P0`, `1D`, `L*`) carried on the routine select the propagator and the output flavor.
