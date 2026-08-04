---
description: ALOHA Lorentz primitive classes (aloha_object.py) — momentum/wavefunction/Dirac/projector/polarisation objects and the aloha_lib LorentzObject/Factory algebra they build on.
---

# Lorentz primitives (aloha_object.py + aloha_lib.py)

Cites `$MADGRAPH_INSTALL/aloha/aloha_object.py` and `aloha_lib.py`, v3.7.1.

## Object pattern
Each primitive is a PAIR: `L_X(aloha_lib.LorentzObject)` holds the tensor representation (`create_representation` builds a `LorentzObjectRepresentation` dict over index tuples → `aloha_lib` Variables), and `X(aloha_lib.FactoryLorentz)` is the user-facing factory (sets `object_class = L_X`, `get_unique_name` for caching/dedup). `LorentzObject.__init__` registers tags via `aloha_lib.KERNEL.add_tag` so the writer knows which momenta/params the routine needs.

## Momentum family (`aloha_object.py:40-500`)
Cite convention below: factory class (user-facing) line; the `L_<name>` representation class sits a few lines above. Line numbers verified against `aloha_object.py` v3.7.1.
- `P` (factory `:62`, repr `L_P` `:40`) — four-momentum `P%d_0..3` as `DVariable`s. `contract_first=1`.
- `PBar` (`:99`, `L_PBar` `:77`) — `(E, -px,-py,-pz)`.
- `PVec` (`:134`, `L_PVec` `:112`) — spatial part (time component 0).
- `Tnorm` (`:162`, `L_Tnorm` `:149`) / `TnormZ` (`:186`, `L_TnormZ` `:173`) — transverse-mode norm and its z-axis variant (polarised production).
- `PSlash` (`:280`, `L_PSlash` `:246`) — `P_mu gamma^mu`.
- `Mass` (`:306`), `Width` (`:447`), `OverMass2` (`:383`, `1/M^2`), `Coup` (`:331`), `Param` (`:472`), `Scalar` (`:500`), `FCT` (`:357`, function hooks), `PT` (`:417`). (All factory lines; verified correct.)
- `FermionWP` (`:210`) / `FermionWM` (`:234`) — fermion-wavefunction +/- modes.

## Wavefunctions (incoming legs)
- `Spinor` (factory `:530`, repr `:510`), `Vector` (`:563`, `:542`), `Spin3Half` (`:614`, `:574`), `Spin2` (`:665`, `:625`). These are the objects multiplied per incoming leg in `compute_aloha_high_kernel`. (Verified correct.)

## Dirac algebra (factory lines; `L_<name>` repr a few lines above)
- `Gamma` (`:716`, `L_Gamma` `:676`), `Sigma` (`:829`, `L_Sigma` `:728`), `Gamma5` (`:857`, `L_Gamma5` `:841`), `C` (charge-conj, `:888`, `L_C` `:868`), `Epsilon` (Levi-Civita, `:985`, `L_Epsilon` `:938`), `Metric` (`:1015`, `L_Metric` `:997`), `Identity` (`:1046`) / `IdentityL` (`:1074`), `ProjM` (`:1103`) / `ProjP` (`:1132`, chiral projectors). `fsign = -1` (`:1294`) sets gamma-matrix sign convention.

## Polarisation / spin-decomposed objects (`:1182-1639`)
- `EPSL` (`:1182`), `EPST1` (`:1232`), `EPST2` (`:1283`) — longitudinal / transverse-1 / transverse-2 polarisation vectors (factory lines; `L_EPSL` repr `:1144`).
- `UFP` (`:1332`), `UFM` (`:1375`), `UFPC` (`:1418`), `UFMC` (`:1461`) and `VFP` (`:1505`), `VFPC` (`:1549`), `VFM` (`:1594`), `VFMC` (`:1639`) — fixed-helicity fermion u/v spinor modes (+ conjugates), for polarised production routines.

## Propagator denominator (`:1650`)
- `DenominatorPropagator` (`:1650`) — `simplify()` (`:1668`) returns `P·P - M^2 + i M Width` (`:1673-1674`). Width/CMS enter here.

## aloha_lib algebra
`aloha_lib.py`: `LorentzObject` (`:1021`), `FactoryLorentz` (`:1063`), `LorentzObjectRepresentation` (`:1086`, tensor as index-tuple dict), `MultLorentz` (`:884`, contraction), `AddVariable`/`MultVariable`/`MultContainer` (`:198`/`:638`/`:618`, the +/* expression tree), `Computation` (`:63`), `SplitCoefficient` (`:1514`, loop-coefficient container), `IndicesIterator` (`:1474`). `KERNEL` is the global computation/tag registry the primitives and high-kernel read.

## vartype dispatch codes (the algebra's type tag)
Each expression-tree node carries a `vartype` int so `__mul__`/`__add__` dispatch without isinstance (`awk` over `aloha_lib.py` v3.7.1):
- `0` — scalar Variable: `C_Variable`/`R_Variable`/`ExtVariable` (`:827`/`:831`/`:835`).
- `1` — `AddVariable` (`:203`), the `+` node (a list of terms).
- `2` — `MultVariable` (`:642`), the `*` node; `MultLorentz` (`:884`) subclasses it.
- `4` — `LorentzObjectRepresentation` (`:1089`), the concrete tensor.
- `6` — `MultContainer` (`:620`).
A bare Python number has NO `vartype` attr; the algebra tests `hasattr(obj,'vartype')` to special-case scalars (e.g. `__mul__` `:1257`).

## Tensor evaluation engine (LorentzObjectRepresentation)
This is HOW a contracted Lorentz expression actually evaluates to numbers/symbols (cited `aloha_lib.py` v3.7.1):
- `__mul__` (`:1253`) — multiplication that performs Einstein/spin summation directly. If `obj` has no `vartype` (a scalar) it scales every component (`:1257-1261`). Else it calls `compare_indices` (`:1387`) on both the lorentz-index lists and the spin-index lists: an index in BOTH lists is summed, an index in only one is free. If NO shared index → `tensor_product` (`:1328`, outer product). If shared → build a new rep over the free indices and fill each via `contraction`.
- `contraction` (`:1295`) — for each assignment of the summed indices (looping `IndicesIterator`), multiplies `self.get_rep` × `obj.get_rep` and accumulates. Minkowski metric sign is applied as `prefactor *= (-1)**(len(l_value) - l_value.count(0))` (`:1322`) — i.e. one sign per SPATIAL (non-zero) lorentz index value summed, encoding `g=diag(+,-,-,-)`. (Spin sums carry no such sign.)
- `IndicesIterator` (`:1474`) — each index runs 0..3 (`__next__` `:1493`); a scalar (len 0) yields a single `[0]` (`nextscalar` `:1507`). So all sums are 4-valued — both lorentz (μ=0..3) and spinor (α=0..3) indices.
- Helpers: `compare_indices` (`:1387`, free-vs-summed split via membership, NOT set XOR for ordering), `pass_ind_in_dict` (`:1414`, index-position→value map), `combine_indices` (`:1423`), `get_rep`/`set_rep` (`:1137`/`:1141`), `listindices` (`:1146`).
