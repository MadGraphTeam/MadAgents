---
description: ALOHA propagator numerators, the aloha global flags (unitary_gauge/loop_mode/mp_precision/complex_mass), and the kernel-vs-writer routing of each flag (kernel=symbolic content, writer=target lowering; complex_mass is writer-only).
---

# Propagators + global flags

Cites `$MADGRAPH_INSTALL/aloha/aloha_object.py`, `create_aloha.py`, `aloha/__init__.py`, v3.7.1.

## Global flags (`aloha/__init__.py`)
Module-level globals read throughout; set by the model loader / output stage before `compute_all`:
- `complex_mass = False` (`:1`) — complex-mass scheme tag.
- `unitary_gauge = True` (`:2`) — gauge selector. INTEGER codes per the `__init__.py` source comment: `0/False` Feynman, `1/True` unitary, `2` axial (kernel uses the `1PS` custom propagator for massless spin-1, `create_aloha.py:315`), `3` Feynman-Diagram gauge / 5D-aloha (bumps `S`/`V` wavefunction sizes to 7 in the writer). (Gauge SELECTION itself is the model-loader slice; ALOHA only consumes the flag.)
- `loop_mode = False` (`:7`) — momenta as complex; sets writer `momentum_size=4` (vs 2).
- `mp_precision = False` (`:8`) — quad-precision parameter passing (selects `*QP` writers).
- `aloha_prefix = 'mdl_'` (`:9`).

## Where each flag branches (kernel vs writer)
Each flag splits effect by a consistent rule: the KERNEL (`create_aloha.py`) owns the SYMBOLIC content (which numerator/wavefunction object, loop-coefficient split); the WRITER (`aloha_writers.py`) owns TARGET LOWERING (array sizes, arg declarations, precision prefix, CMS real-vs-complex emission). Verified by grepping `aloha.<flag>` across both files (v3.7.1):
- `unitary_gauge` — BOTH. Kernel: numerator choice (`:315` axial `1PS`, `:348` massless vector). Writer: FD-gauge (`==3`) layout/declarations (`:551,567,574,679,726,895,942`, also `type_to_size` bump `:45`).
- `loop_mode` — BOTH but mostly WRITER. Kernel: tail loop-coefficient return (`:418`) + temporary toggles around L-tags (`:824,984,1013`). Writer: `momentum_size=4` (`:40`) and dozens of layout sites (`:565,572,580,693,870,1159…`).
- `complex_mass` — WRITER ONLY (`:233` pass M complex-vs-double, `:853,1222,1789,2315` denom/coup emission). NOT in `create_aloha.py`/`aloha_object.py` (grep confirms none); the denominator EXPRESSION always carries `+i·M·Width` (`aloha_object.py:1668`), CMS only changes declaration/division.
- `mp_precision` — BOTH. Kernel: adds `MP` tag (`:102`). Writer: selects `*QP` emitter (`:456`).

So "everything branches in the high kernel" is FALSE: the kernel only steers symbolic content (and not on `complex_mass` at all).

## Propagator numerators (aloha_object.py:1690-1733, lambdas)
- `SpinorPropagatorout` (`:1690`) = `-(γ·P - M·1)`; `SpinorPropagatorin` (`:1693`) = `(γ·P + M·1)`.
- `VectorPropagator` (`:1697`) = `i(-g_{l1 l2} + P_{l1}P_{l2}/M^2)` (massive, unitary). `VectorPropagatorMassless` (`:1700`) = `-i g_{l1 l2}` (Feynman/massless).
- `Spin3halfPropagatorin/out` (`:1703`/`:1710`) — massive Rarita-Schwinger; `...MasslessOut/In` (`:1718`/`:1719`).
- `Spin2masslessPropagator` (`:1722`) = `1/2(g_{μα}g_{νβ}+g_{μβ}g_{να}-g_{μν}g_{αβ})`; `Spin2Propagator` (`:1727`) adds the massive `1/M^2` and `1/6` trace terms.

## Denominator
`DenominatorPropagator.simplify()` (`:1668`) → `P·P - M^2 + i·M·Width`. Width and CMS imaginary part live HERE, separate from the numerator. The high kernel sets `self.denominator` per outgoing leg (`create_aloha.py:320` massless→None; standard massive→None — the denom is applied at the matrix-element/HELAS stage, ALOHA emits the numerator+denom factor).

## Custom-propagator tags (`create_aloha.py`)
`get_custom_propa` (`:453`) resolves tag-coded propagators. Tags from `compute_all` custom_propa block (`:912-930`): `P0` massless, `P1N` numerator-only (hel recycling), `P1L/P1T/P1A/P1PS` vector longitudinal/transverse/axial/phase-space, `P1P/P1M` fermion ±, `1D` BW-cutoff multiplier (applied around the standard propagator, `:326-329`,`:380-382`). `create_prop_library` (`:1374`) precomputes `Spin2Prop`/`Spin2PropMassless` expansions into `lib`.

## Caution
Gauge and mass branch in the HIGH KERNEL, not the writer (`create_aloha.py:347-351` vector; `:368-375` spin-2). A zero-mass particle (`part.mass.name.lower()=='zero'`) takes the massless propagator path regardless of gauge for vectors when `unitary_gauge in [0,3]` (`:348`). Always confirm the active `aloha.unitary_gauge` integer code and the particle mass before predicting which propagator numerator a routine carries.
