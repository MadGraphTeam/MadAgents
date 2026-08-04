---
description: How the ALOHA Fortran writer lowers the symbolic kernel to code — momentum packing/reconstruction, denom-vs-CMS emission, P1N/P1D/BWCUTOFF args, write_combined sum-emission, loop COEFF 3D-array, FCT/TMP zero-elimination self-retry.
---

# Writer lowering mechanics (aloha_writers.py)

Cites `$MADGRAPH_INSTALL/aloha/aloha_writers.py` v3.7.1. Companion to writer-hierarchy.md (which maps the CLASSES); this page is the LOWERING (how one symbolic kernel becomes Fortran lines). Section order of an emitted routine fixed by `write` (`:250-261`): header → declaration → momenta → body (`define_expression`) → foot → symmetries.

## Momentum packing/reconstruction — `get_one_momenta_def` (`:689`)
The 4-momentum of a leg is NOT a separate argument — it is unpacked from the leg's complex wavefunction array. Non-loop mode (`:696-711`):
- `P_i(0) = sign*dble(W_i(1))`, `P_i(1) = sign*dble(W_i(2))`, `P_i(2) = sign*dimag(W_i(2))`, `P_i(3) = sign*dimag(W_i(1))`.
- So the 4-momentum lives packed in the FIRST TWO complex slots of every wavefunction array (real/imag halves), which is why `momentum_size=2` (`:40`) and the physics payload starts at index 3.
- Loop mode (`:693-694,712-715`): each component is its OWN complex slot `P_i(j)=sign*W_i(1+j)`, hence `momentum_size=4`.
- `sign` from `get_P_sign` (`:165`): `-` for the off-shell/outgoing leg, `+` otherwise (the conjugate-flip branch is commented-out dead code `:172-180`).

## Off-shell momentum from conservation — `get_momenta_txt` (`:612`)
- `get_momentum_conservation_sign` (`:124`): `global_sign=-1`; every incoming leg gets `sign=-1*global_sign=+1` → emits `+`/`-` so the off-shell momentum = (signed) sum of incoming momenta. The fermion-specific branch is dead (`if 1:` short-circuits, `:140`); outgoing leg emits `0*` placeholder (`:155`).
- Off-shell wavefunction's momentum slots written first (`:650-653`), then `get_one_momenta_def` re-derives `P_out` from them (`:654-655`).
- `OM_i` (= 1/M^2) emitted guarded: `OM_i=0; if (M_i.ne.0) OM_i=1/M_i**2` (`:624-626`) — only when `declaration.is_used`.

## denom emission (the propagator denominator) — `define_expression` (`:851-877`)
For an off-shell, non-loop routine:
- Standard (no CMS): `denom = COUP/(P_out(0)**2-P_out(1)**2-P_out(2)**2-P_out(3)**2 - M_out*(M_out - CI*W_out))` (`:859`) — Breit-Wigner with width, OR `COUP/(written denominator obj)` if `routine.denominator` set (`:856`). Result multiplied as `coeff='denom*'`.
- complex_mass scheme (`:861-867`): `denom = COUP/(...P^2... - M_out**2)` — M_out is the COMPLEX pole mass (no explicit width term; the imaginary part is inside M_out). A custom `routine.denominator` + CMS raises (`:864`, incompatible).
- `P1N` (numerator-only / hel-recycling): NO denom emitted; `coeff='COUP*'` instead (`:855,865,868,877`). The routine returns the bare numerator for the caller to divide.

## Off-shell argument list — `define_argument_list` (`:195`, `:230-243`)
The off-shell routine's trailing args encode the denominator inputs:
- standard: `M_out` (double) + `W_out` (double) (`:236-240`).
- complex_mass: single COMPLEX `M_out`, no width (`:233-235`).
- `P1N`: neither — pass nothing (`:231-232`).
- `P1D` (BW-cutoff tag): adds a `BWCUTOFF` double argument (`:241-243`) — the BW-cutoff widening surfaces as a routine parameter.
- Incoming legs are `list_complex W_i`; a `C`-conjugate leg passes its PARTNER's array (`:207-213`, Majorana flow swap).

## body element emission — `define_expression` (`:832-903`)
- amplitude (no off-shell leg): `vertex = COUP*(numerator[0])` (`:832-840`).
- off-shell: each output array component `out(pass_to_HELAS(ind)+shift) = coeff*formatted` (`:897-899`); `shift=1` normally, `shift=5` if FD gauge and scalar output (`:895-896`).
- `pass_to_HELAS` (`:81`) maps a Lorentz index to `index+start+momentum_size` — i.e. payload after the packed momentum.

## FCT/TMP zero-elimination self-retry (`:905-927`)
After building the body, the writer scans the emitted text: any contracted-TMP or FCT helper variable that appears EXACTLY ONCE (defined but never used — typically because a term multiplied to zero) is deleted from `routine.fct`/`routine.contracted` and `define_expression` RECURSES (`:925-927`). So the final routine prunes dead temporaries the symbolic layer left behind.

## write_combined (multiple-Lorentz sum) — `:954`
One routine summing several sub-Lorentz contributions sharing an off-shell leg. Header takes `COUP1..COUPn` (`:971`). It `call`s each sub-routine `name<tag>_<offshell>` into `tmp` then accumulates:
- amplitude: `vertex = vertex + tmp` (`:1008`).
- off-shell wavefunction: element-wise `do i=momentum_size+1,momentum_size+size: out(i)=out(i)+tmp(i)` (`:1010-1014`) — sums only the PHYSICS slots (skips the packed momentum). `size = type_to_size[out] - 2`.
- Appends to the file (`'a'` mode, `:1032`) since the sub-routines already exist there.

## loop COEFF 3D-array lowering — ALOHAWriterForFortranLoop.define_expression (`:1068`)
The loop writer turns the kernel's `SplitCoefficient` into `COEFF(component, J, K)`:
- `rank = expr.get_max_rank()`; `nb_coeff = q_polynomial.get_number_of_coefs_for_rank(rank)` (`:1108-1110`) — `q_polynomial` is the OpenLoops rank-counting helper; J in `0..nb_coeff-1` indexes the rank-graded loop-momentum monomials.
- `size = type_to_size[l_id leg]-2`; K in `0..size-1` indexes the off-shell wavefunction physics component.
- Emits `COEFF(<helas-component>, J, K+1) = coup*<expr>` (`:1126-1133`). This is the concrete realization of `compute_loop_coefficient`'s `SplitCoefficient` (see high-kernel-algorithm.md) — the rank-graded numerator coefficients OpenLoops/MadLoop consumes.

## Cautions
- The momentum-packing convention (`dble`/`dimag` of slots 1-2) is a STATIC writer fact, but the exact emitted text in a `<PROC_DIR>/Source/DHELAS/*.f` is a runtime instantiation — to assert a specific generated line, probe (cheap `output` of a 1-vertex model) rather than claim from reading.
- `get_foot_txt` under FD gauge (`unitary_gauge==3`) emits an extra `CALL MULTIPLY_PROPAGATOR_FACTOR(...)` for V/S off-shell legs (`:942-948`) — FD-gauge routines carry a trailing propagator-factor multiply not present in other gauges.
