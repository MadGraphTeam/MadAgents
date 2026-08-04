---
description: A model's coupling_orders.py expansion_order silently caps the EFT amplitude order when no constraint is given (SMEFTatNLO NP=2 → auto NP<=2; dim6top DIM6=99 → no cap); hierarchy values build the WEIGHTED order.
---

# EFT default cap: expansion_order auto-truncation + WEIGHTED from hierarchy (v3.7.1)

Each UFO `coupling_orders.py` declares two integers per order — `expansion_order` and `hierarchy`.
Both drive silent default behaviour when the user gives NO explicit order constraint. EFT-critical:
they decide whether an EFT order is auto-truncated and at what value.

## expansion_order = the model-builder's default amplitude cap

`$MADGRAPH_INSTALL/models/import_ufo.py:662-676`: for every `order` in `all_orders`,
`expansion_order[order.name] = order.expansion_order`, then `model.set('expansion_order', ...)`.
The `try` populates from the UFO attribute; it only raises if `perturbation_couplings` is on AND
the attribute is missing — so a tree (LO) model with the attribute still gets it populated.
(Tree models lacking the attribute fall through `except ... else: pass`; then the lazy default at
`base_objects.py:1231-1234` sets every order to `-1` = "no cap".)

`base_objects.py:check_expansion_orders()` (def line 3757), called at
`diagram_generation.py:1688` and `:2089` during process build:
- `tmp = [(k,v) for (k,v) in expansion_orders.items() if 0 < v < 99]` (line 3766) — only orders
  with a finite cap strictly between 0 and 99 are enforced. **99 is the sentinel for "no cap".**
  **`expansion_order = 0` is ALSO excluded** (`0 < 0` is False) → an order declared with
  expansion_order=0 gets NO amplitude cap via this path, i.e. it behaves like 99/unconstrained, NOT
  "auto-excluded". This refutes the common doc claim that SMEFTsim's `NPprop = CouplingOrder(expansion_order=0)`
  "auto-excludes propagator corrections unless NPprop<=2 is requested": via THIS core path, expansion_order=0
  imposes no default cap at all. (Whether SMEFTsim excludes NPprop by a different mechanism — e.g. the
  order simply not appearing on any surviving vertex, or a restrict card — is the coupling-order slice's
  definitive call + a GAP until SMEFTsim is installed; the EFT consequence here is only that the
  expansion_order=0 value itself does not cap.)
- For each such `(k,v)`: if the user's `orders[k] > v` (or `k` absent from orders), it sets
  `orders[k] = v` and warns. Two warning texts (lines ~3772/3779):
  - if a squared order exceeds the cap: "...can potentially receive contributions with powers of
    the coupling larger than the maximal value allowed by the model builder (%v). Hence MG5_aMC
    sets the amplitude order for that coupling to be this maximal one."
  - else: "The coupling order (%k=%v) specified is larger than the one allowed by the model
    builder. The maximal value allowed is %s. We set the %k order to this value."

## The two dim-6 EFT models differ here (probe-verified; NOT bundled — fetch first, see bundled-eft-models)

- **SMEFTatNLO**: `coupling_orders.py` → `NP = CouplingOrder(expansion_order=2, hierarchy=1)`,
  `QCD(expansion_order=99, hierarchy=2, perturbative_expansion=1)`, `QED(expansion_order=99, hierarchy=4)`.
  Because NP's expansion_order=2 is in `(0,99)`, **NP is auto-capped at 2 with no user constraint**.
  Probe `import model SMEFTatNLO-LO; generate p p > t t~` (no NP given) — MG emits:
  `Trying process: g g > t t~ NP<=2 WEIGHTED<=2 @1`. The `NP<=2` is the expansion_order cap injected
  automatically. So a bare SMEFTatNLO process is the quadratic (NP^2) regime by default, NOT unlimited.
- **dim6top_LO_UFO**: `coupling_orders.py` → all four orders (QCD,QED,DIM6,FCNC) `expansion_order=99`.
  DIM6=99 is the no-cap sentinel → DIM6 is NEVER auto-capped. Probe
  `import model dim6top_LO_UFO; generate p p > t t~` — process line is `g g > t t~ WEIGHTED<=2 @1`
  with **no `DIM6<=N`** term. DIM6 is unbounded unless the user constrains it.

## hierarchy → the WEIGHTED order weights (find_optimal_process_orders)

`hierarchy` is the per-order weight in the synthetic `WEIGHTED` order MG uses to find the minimal
coupling combination that yields diagrams (`base_objects.py:get_WEIGHTED_order` line 893:
`sum(model['order_hierarchy'][k]*orders[k])`; `coupling_orders['WEIGHTED']=weight` line 2654-2656).
Default hierarchy if UFO omits it: all=1, with QED bumped to 2 ONLY when the model's order set is
exactly `{QCD,QED}` (`get_order_hierarchy` line 1382-1386: `hierarchy[QED]=2` guarded by
`if set(coupling_orders)==set(['QCD','QED'])`). So for any EFT model (which carries NP/DIM6 beyond
QCD/QED) the default path would give QED=1 — but EFT UFOs declare their own hierarchy, so this default
rarely fires for them.
Probe-confirmed the WEIGHTED expression printed during generation matches the UFO hierarchy values:
- SMEFTatNLO: `WEIGTHED IS NP+2*QCD+4*QED` (NP=1, QCD=2, QED=4 — the declared hierarchies).
- dim6top: `WEIGTHED IS QCD+2*QED+DIM6+FCNC` (QCD=1, QED=2, DIM6=1, FCNC=1 — declared hierarchies).
(Note "WEIGTHED" is MG's own typo in the INFO line.) `find_optimal_process_orders` then raises the
WEIGHTED ceiling until diagrams appear (`Trying coupling order WEIGHTED<=2`), which is how a bare
`p p > t t~` gets its SM-level `WEIGHTED<=2`.

## Caution / boundary

- A bare SMEFTatNLO process silently includes NP up to 2 — if a user expects "SM only" from
  `generate p p > t t~` they get SM+linear+quadratic EFT instead. Pin `NP==0` for SM-only.
- Asking for MORE than the cap is also silently clamped. Probe `generate p p > t t~ NP==4`
  (SMEFTatNLO-LO): warns verbatim "The process with the squared coupling order (NP^2==8) specified
  can potentially recieve contributions ... larger than the maximal value allowed by the model
  builder (2). Hence MG5_aMC sets the amplitude order for that coupling to be this maximal one." and
  the process line becomes `g g > t t~ NP<=2 NP==4` — the amplitude is clamped to NP<=2 while the
  user's NP==4 token is retained, so NP==4 is effectively unreachable for this model. The model
  builder's expansion_order=2 is a hard ceiling no user constraint can exceed.
- This is amplitude-order capping. The amp_split / squared-order accounting downstream is nlo-export
  slice; whether linear vs quadratic truncation is physically wanted is ma-physics-consultant's call.
- `hierarchy` perturbative_expansion (QCD has `perturbative_expansion=1` in SMEFTatNLO) flags the NLO
  expansion variable — loop-mechanics territory, not enforced by check_expansion_orders.
