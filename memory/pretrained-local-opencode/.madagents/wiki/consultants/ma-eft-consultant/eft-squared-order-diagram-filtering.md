---
description: Diagram-survival side of EFT truncation — apply_squared_order_constraints' three filters (amplitude ==/>, positive squared, negative squared) realizing linear vs quadratic vs highest-order truncation; probe-verified dim6top counts.
---

# EFT squared-order diagram filtering (the survival side of truncation)

My parser page (eft-power-counting-parser.md) records how `NP==v` / `NP^2==2v` *parse*; the
expansion-order page records the auto-cap. THIS page is the missing third piece: how the parsed
constraints actually KEEP or DROP diagrams — the mechanism that realizes linear vs quadratic vs
"highest-order" EFT truncation as different diagram sets.

## Call site (LO only — skipped for NLO)
`$MADGRAPH_INSTALL/madgraph/core/diagram_generation.py:807-808`:
```
if not returndiag and len(res)>0:
    res = self.apply_squared_order_constraints(res)
```
- Runs after `diagram.calculate_orders(model)` (line 797-798) sets each diagram's amplitude orders.
- **Skipped when `returndiag=True`** — the NLO path. Comment 804-806: at NLO "the interference are
  not necessarily among the diagrams generated here only," so the squared filter cannot be applied on
  this local diagram list. EFT-NLO truncation is enforced elsewhere (amp_split, nlo-export slice), NOT
  by this LO filter. This is the boundary where my slice hands the squared-order enforcement to nlo-export.
- Inline comment 801-803 documents the negative convention: `OrderName=-n` means "everything up to the
  N^(n+1)LO contribution in that order, and at most one order can be restricted this way."

## `apply_squared_order_constraints` (diagram_generation.py:856-902) — three filters in order
1. **Amplitude `==` / `>`** (constrained_orders) → `filter_constrained_orders`
   (base_objects.py:2897-2910). Operates on the diagram's OWN amplitude order (not a square):
   keeps `diag['orders'][order] == value` (for `==`) or `> value` (for `>`). This is the LINEAR
   filter: `NP==1` (== amplitude) keeps only single-insertion amplitudes → SM×EFT interference regime.
2. **Positive squared** → `apply_positive_sq_orders` (base_objects.py:2882-2895), iterated in a
   `while` loop (864-881) because one order's filter can change another's. Each tested diagram is kept
   if it pairs with SOME reference diagram passing `pass_squared_order_constraints`.
3. **Negative squared** (at most one) → `apply_negative_sq_order` (base_objects.py:2863-2880).

## `pass_squared_order_constraints` (base_objects.py:2659-2676) — the squared order = SUM of two amps
The squared order of a contribution is `self.get_order(order) + diag_multiplier.get_order(order)`
(line 2670-2671) — the EFT power of diagram A times diagram B is the SUM of their amplitude powers.
- `==` keeps iff `combined == value` (line 2672). For a model with per-insertion +k, `NP^2==2k` keeps
  exactly the order-2k squared terms: amplitude-pairs whose NP powers sum to 2k — i.e. EFT(NP=k)×EFT(NP=k)
  plus SM(NP=0)×(NP=2k) if a two-insertion amplitude exists. The QUADRATIC regime = full squared EFT at
  the target order (includes EFT×EFT, not just SM×EFT interference).
- `<=`/`=` keeps `combined <= value`; `>` keeps `combined > value`.
- **Negative-valued squared orders are SKIPPED here** (line 2668-2669 `if value<0: continue`) —
  they go through `apply_negative_sq_order` instead.

## Negative squared order = "up to N^(n+1)LO" (apply_negative_sq_order, base_objects.py:2863-2880)
`target_order = min(ref_diag_list.get_order_values(order)) + min(self.get_order_values(order)) + 2*(-value-1)`
(line 2874-2875). It computes the LO squared order (min+min) then adds `2*(-value-1)` to climb n-1
NLO rungs, then applies `apply_positive_sq_orders` with that positive target. Docstring example:
`QED^2<=-2` = "up to NLO in QED" → target 4. **The target is computed per subprocess** because min
orders differ between subprocesses. The computed positive target is written back into
`squared_orders` (diagram_generation.py:897) so the printout and output stage see a positive value.

## Probe-verified contrast (dim6top_LO_UFO, `p p > t t~`, v3.7.1) — three truncations, three counts
DIM6 per-insertion = +1 (bundled-eft-models.md). Same process, three constraints, distinct diagram sets:
| constraint | regime | gg diagrams | uu~ diagrams |
|---|---|---|---|
| `DIM6==1` (amplitude ==) | linear / interference | 6 | 6 |
| `DIM6^2==2` (positive squared) | quadratic (full squared at order 2) | 15 | 6 |
| `DIM6^2<=-1` (negative) | "highest order" / up to LO+ | 7 | 10 |
- The `DIM6^2<=-1` INFO line resolves DIFFERENTLY per subprocess: `g g > t t~ DIM6<=99 DIM6^2<=-1`
  but `u u~ > t t~ DIM6<=99 DIM6^2<=0` — confirming the per-subprocess `target_order` computation
  (gg and uu~ have different min-DIM6 SM orders, so the climbed target differs).
- gg quadratic (15) > gg linear (6): the squared filter admits more diagrams than the amplitude `==`
  filter because the squared regime keeps both SM and EFT amplitudes that multiply to the target order.

## LO per-order ME splitting without diagram pruning: `[tree=NP]`
Distinct from the diagram-pruning filter above. `generate p p > t t~ [tree=NP]` keeps LoopOption='tree'
(LO, no loops) but routes NP into `split_orders` so matrix.f evaluates each NP-power ME piece
separately WITHOUT pruning the diagram list. Probe `dim6top_LO_UFO; generate p p > t t~ [tree=DIM6]`
→ INFO `Trying coupling order WEIGHTED<=2` then `g g > t t~ WEIGHTED<=2` with 15 gg diagrams (the FULL
SM+EFT set, DIM6 unbounded) — no `DIM6==N` / `DIM6^2==N` pruning, just the WEIGHTED<=2 ceiling. So
`[tree=DIM6]` = "all diagrams, split the ME by DIM6 power"; `DIM6^2==2` = "prune to the order-2 squared
diagrams". Use `[tree=NP]` when you want every order piece reported separately at LO.

## The split_orders contract (base_objects.py:2996-3005, verbatim docstring)
"The user might want to have the individual matrix element evaluations for specific values of the
coupling orders... For example, for the process `p p > j j [] QED=2` (QED=2 is then a squared order
constraint), then QED will appear in the 'split_orders' list so that the subroutine in matrix.f return
the evaluation of the matrix element individually for the pure QCD contribution 'QCD=4 QED=0', the pure
interference 'QCD=2 QED=2' and the pure QED contribution of order 'QCD=0 QED=4'." Directly applies to
EFT: `NP^2<=4` puts NP in split_orders → matrix.f returns pure-SM, SM×EFT interference, and pure-EFT²
pieces separately. The per-order ME *consumption* (amp_split, matrix.f generation) is nlo-export slice;
this page records only that any `NP^2` squared constraint (LO) or any NLO process forces NP into
split_orders (NLO forces ALL model orders — see eft-nlo-order-determination.md).

## Cautions / boundary
- This filter is LO-only. For `[QCD]`/`[QED]` NLO processes the squared-order enforcement is NOT here;
  it lives in amp_split / matrix-element split_orders (nlo-export slice). Do not promise that an
  `NP^2==4` constraint prunes diagrams the same way at NLO — at LO it prunes the local list, at NLO
  the interferences span generation boundaries and the constraint is applied at the ME-evaluation level.
- `split_orders` (Process default_setup, base_objects.py:3005 + docstring 2996-3004) is the list of
  order names whose ME contributions are evaluated SEPARATELY in matrix.f (e.g. pure-QCD, interference,
  pure-EFT pieces). That per-order ME splitting is nlo-export territory; this page only covers the
  diagram-list pruning at generation time.
- Whether linear (interference) or quadratic (squared) truncation is physically wanted is
  ma-physics-consultant's call; this page records only the mechanism and the observable diagram counts.
