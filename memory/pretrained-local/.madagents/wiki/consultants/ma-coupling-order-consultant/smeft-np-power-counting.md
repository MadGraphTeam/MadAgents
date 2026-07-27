---
description: SMEFT NP coupling-order power counting in extract_process — NP=1 vs NP^2<=2 vs NP^2==N vs NP==1; the convention→bin map (σ_int=NP^2==1·p, σ_quad=NP^2==2·p; p=NP-per-insertion read from the model's couplings.py, odd bins empty when p even); single-run subtraction (σ_int=σ(NP^2<=1)−σ(NP=0), σ_sig=σ(NP^2<=2)−σ(NP^2<=1)) via the squared→amplitude injection (4994-4999: no-amp-order+squared → orders[k]=sq_value, or 99 for neg/'>'); NP=1 row is p-dependent (SM-only p=2 vs full total p=1, doc "NP=1=total" holds only for p=1); the ==/<= c=0 discriminator (σ(c=0)≡0 vs SM-leaks); squared-== isolation via squared_orders+pass_squared_order_constraints(2670-2674) NOT constrained_orders (conflation trap); NP^2==N LO-accepted (squared, not constrained_orders, no 4983 gate); per-operator ^2== same path; AMPSPLITORDERS fingerprint scope; expansion_order cap; WEIGHTED QCD-only auto-detect; restrict_default removing NP.
---

# SMEFT NP power-counting through the order parser

`NP` (the dim-6 Wilson-coefficient insertion count) is NOT special-cased anywhere
in `extract_process` — it is an ordinary `model_orders` key, so every mechanism on
the generic pages applies to it verbatim. What IS non-obvious is (a) which generic
mechanism each SMEFT idiom routes through, and (b) a model-side cap
(`expansion_order`) and a WEIGHTED auto-detect that interact with the NP order and
are NOT visible from the parser alone. This page ties them together for the EFT
case; the parse mechanics live on the generic pages cross-referenced below.

## The model declares NP (SMEFTatNLO)
Read the order declarations fresh in
`$MADGRAPH_INSTALL/models/SMEFTatNLO/coupling_orders.py` — each
`CouplingOrder(name=..., expansion_order=..., hierarchy=...)`. The version-STABLE
facts (drop the bare weights/caps — they are per-model and drift-prone, read at need):
- The model declares an umbrella `NP` order plus `QCD`, `QED`.
- `hierarchy`: NP is the CHEAPEST coupling in the WEIGHTED ordering (lowest
  weight, below QCD and QED). Read the three weights from `coupling_orders.py`.
  This UFO-supplied hierarchy overrides the `get_order_hierarchy` default
  (base_objects.py 1379-1386), so the `{QCD,QED}` special case never applies here.
- `expansion_order`: NP carries a FINITE model-builder cap (the highest NP power
  any single process may carry); QCD/QED use the `99` "infinite" sentinel. Read
  NP's cap from `coupling_orders.py`.
  (dim6top_LO_UFO instead declares `DIM6`/`FCNC` with the `99` no-cap sentinel —
  no built-in cap; the order name there is `DIM6`/`FCNC`, not `NP`.)

`$MADGRAPH_INSTALL/models/import_ufo.py` 662-676 loads each
`CouplingOrder.expansion_order` into `model['expansion_order']` and `.hierarchy`
into `model['order_hierarchy']` (660). The default `expansion_order` when a UFO
omits it is `-1` per order (base_objects.py 1231-1234).

## The OTHER bundled EFT model: `dim6top_LO_UFO` (different conventions)
Read `$MADGRAPH_INSTALL/models/dim6top_LO_UFO/coupling_orders.py` fresh: it
declares FOUR orders — `QCD`, `QED`, `DIM6`, `FCNC` — none named NP, all using
the `99` no-cap sentinel for `expansion_order`. Read the per-order `hierarchy`
weights from the file (drop the bare weights).
Three EFT-relevant contrasts with SMEFTatNLO, all source-confirmed:
- **Order NAMES differ**: the EFT-insertion order is `DIM6` (and a separate
  `FCNC`), NOT `NP`. So the EFT idiom on this model is `DIM6=1` / `DIM6^2==2`,
  and `NP=...` would be rejected as not-valid. The order name is per-model — never
  assume `NP`.
- **NO `expansion_order` cap**: all four use `99` (the "infinite" sentinel), so
  the `check_expansion_orders` clamp (`0<v<99` filter) NEVER fires for DIM6 — no
  built-in dim-6-truncation cap, unlike SMEFTatNLO's finite NP cap. A user must impose
  the truncation order explicitly.
- **NO restrict cards**: `ls models/dim6top_LO_UFO/restrict_*.dat` returns nothing
  — so there is no default restriction stripping the DIM6
  order, and the `restrict_default REMOVES NP` caution below is SMEFTatNLO-ONLY.
  `import model dim6top_LO_UFO` keeps DIM6 live with no `-LO`/`-NLO` suffix.
- hierarchy: read the per-order weights from `coupling_orders.py`; on this model
  DIM6/QCD/FCNC share the cheapest weight and QED is heavier, giving a
  hierarchy-keyed WEIGHTED formula (per `split-orders-and-weighted.md`).

PROBE-CONFIRMED: `import model dim6top_LO_UFO` (no suffix);
`generate g g > t t~ DIM6=1` -> `Interpreting 'DIM6=1' as 'DIM6<=1'`, 13 diagrams.
`generate g g > t t~ NP=1` -> `InvalidCmd : model order NP not valid for this
model (valid one are: DIM6, QCD, FCNC, QED, EW, EW^2, aEW, aS)` — DIM6+FCNC live,
NP not, EW/aEW/aS aliases present. The 4-element model_orders prefix
(`DIM6/QCD/FCNC/QED`) is subject to the SAME `list(set(...))` non-determinism as
the SMEFTatNLO case above — this run's order is not the stable emit; only the
NAMES present and the `EW, EW^2, aEW, aS` alias tail are load-bearing.

## CAUTION: `restrict_default` REMOVES the NP order (PROBE-CONFIRMED)
`import model SMEFTatNLO` loads `restrict_default.dat`, which zeroes all DIM6
Wilson coefficients. With no surviving NP-carrying vertex, `NP` drops out of the
model's `coupling_orders`, so the parser rejects it:
```
generate u u~ > t t~ NP=1
InvalidCmd : model order NP not valid for this model
  (valid one are: QCD, QED, EW, EW^2, aEW, aS). Please correct
```
**The valid-set ordering is NON-DETERMINISTIC across launches** (9 separate
MadGraph launches): the SAME command emits both
`QCD, QED, EW, EW^2, aEW, aS` (7 of 9) and `QED, QCD, EW, EW^2, aEW, aS` (2 of 9).
Neither prefix order is reliable. Root cause: the message's `valid` list is
`list(model_orders) + list(coupling_alias.keys())` (`madgraph_interface.py` 4943,
amplitude branch). `model_orders = self._curr_model.get('coupling_orders')` is
`list(set(...))` — `get_coupling_orders` returns a `set`
(`base_objects.py` 1376), and this build runs with active hash randomization
(`sys.flags.hash_randomization=1`, `PYTHONHASHSEED` unset, launcher does not pin
it), so the `{QCD, QED}` prefix reorders per interpreter launch. The
`coupling_alias` TAIL (`EW, EW^2, aEW, aS`) IS stable — it is plain dict insertion
order from the alias-build block (`madgraph_interface.py` 4896-4907). So: do not
carry ANY prefix order as load-bearing; only "those names are in the valid set"
and "the alias tail keeps its EW/EW^2/aEW/aS sequence" are reliable.
Fix: load an NP-keeping restriction — `import model SMEFTatNLO-NLO` (or `-LO`)
makes `NP=1` parse (probe: `Interpreting 'NP=1' as 'NP<=1'`, 3
diagrams for `u u~ > t t~`). This is the order-name validity check at
`madgraph_interface.py` — the `raise` is at 4944 (amplitude branch) / 4931
(squared branch); 4942/4929 are the guard tests (`if name not in model_orders`
/ `if basename not in ...`) — firing against the RESTRICTED model's order set,
not the raw UFO. (The valid-set message also shows SMEFTatNLO supplies
`EW`/`aEW`/`aS`, so the EW<->QED + aS/aEW aliases of `coupling-aliases.md` are
live here too.)

## The three SMEFT idioms — which dict each routes through (RULE); counts for ONE topology only
The RULE (version-stable, general): `NP=n` bounds the AMPLITUDE at generation
(interference bin after squaring); `NP^2<=/==n` lets the full amplitude generate
then cuts at the SQUARED-ME level (different, larger diagram set); amplitude
`NP==n` adds a post-gen exactly-n filter. The Diagrams column below is
PROBE-CONFIRMED for **this ONE topology** (SMEFTatNLO-NLO, `u u~ > t t~`) — an
example, NOT a class recipe; DERIVE the count per process/model from its topology,
never reuse these integers.
| Syntax | Routes through | Stored | Diagrams (this topology only) | Meaning |
|---|---|---|---|---|
| `NP=1` | `=`->`<=` (amp) | `orders['NP']=1` | 3 | amplitude has ≤1 EFT insertion -> linear-in-Wilson interference with SM after squaring |
| `NP^2<=2` | `^2` squared | `squared_orders['NP']=(2,'<=')` | 13 | squared ME truncated at NP^2≤2 (full amp generated, then ME-level cut) |
| `NP^2==2` | `^2` squared | `squared_orders['NP']=(2,'==')` | 13 | keeps ONLY the combined-NP^2=2 bin in |M|^2 (= σ_int on SMEFTatNLO p=2; = σ_quad on SMEFTsim p=1 — convention→bin map below). PARSES clean at LO, no `Interpreting` rewrite (`==`∈`_valid_sqso_types`) |
| `NP==1` | `==` (amp) | `constrained_orders['NP']=(1,'==')` + auto `squared_orders['NP']=(2,'==')` + `orders['NP']=1` | NoDiagram | exactly-one-NP filter |

Key contrasts:
- **`NP=1` (3 diag) vs `NP^2<=2` (13 diag)**: `NP=1` BOUNDS THE AMPLITUDE to ≤1
  insertion, pruning generation early (3 diagrams). `NP^2<=2` lets the full
  amplitude generate (13 diagrams, incl. NP=2 pieces) and applies the constraint
  at the SQUARED-ME level. They are DIFFERENT PHYSICS and DIFFERENT diagram sets —
  this is the interference-vs-squared trap, framed for SMEFT.
- **`NP^2==2`**: on SMEFTatNLO this isolates the dim-6×SM interference (cross
  term, one Wilson factor) — but ONLY because SMEFTatNLO uses NP=2-per-insertion
  (see "convention→bin map" below). The bin↔physics identity is
  CONVENTION-DEPENDENT: on a NP=1-per-insertion model (SMEFTsim/dim6top) the
  interference bin is `NP^2==1` and `NP^2==2` selects the dim-6-SQUARED piece.
  Mirror of the SM `QED^2==2 QCD^2==2` example at `help_generate` 611-616 (which
  works because SM has QED=1-per-vertex).
- **`NP==1` -> NoDiagramException** (probe): it PARSES (LO tree), the `==` branch
  (`equals-interpretation-and-strict-equality.md`) auto-spawns
  `NP^2==2` (the 2N doubling, `amplitude-to-squared-doubling.md`) and sets
  `orders['NP']=1`, so the trial process is `u u~ > t t~ NP=1 NP==1 NP^2==2`. Then
  the post-generation `constrained_orders` FILTER
  (`constrained-orders-consumption.md`) keeps only diagrams with EXACTLY NP=1 —
  and `u u~ > t t~` has none (the QCD tree is NP=0; no single-insertion diagram
  survives), so `NoDiagramException`. This is the filter-not-generation-bound
  mechanism manifesting in SMEFT. (Tree-only: `==`/`>` rejected at NLO,
  `extract_process` 4983-4985.)

## How `^2` changes which |M|^2 bin survives (the 2N principle for SMEFT)
`NP^2=K` constrains the SQUARED-amplitude NP power directly
(`squared_orders['NP']=(K,...)`). The squared power of a |M|^2 term is the SUM of
the amplitude NP orders on the two factors:
`combined_order = amp_left.NP + amp_right.NP`
(`base_objects.py pass_squared_order_constraints 2670`).
`NP^2==K` keeps ONLY the bin with `combined_order==K`; `NP^2<=K` keeps every bin
with `combined_order<=K` (INCLUDING the SM×SM bin at 0). Negative `NP^2==-I`
selects the N^(-I+1)LO term (`negative-order-values.md`).

The 2N doubling (`amplitude-to-squared-doubling.md`) is why an amplitude `NP==1`
auto-spawns the squared `NP^2==2`: exactly-one amplitude-NP-unit → combined=2 in
|M|^2 (1+1). This is pure arithmetic on the AMPLITUDE NP order, NOT on the
"number of operator insertions" — the two coincide only when NP-per-insertion=1.

`combined_order = self.get_order(order) + diag_multiplier.get_order(order)`
(`base_objects.py pass_squared_order_constraints` 2670-2671) — the sum of the two
amplitude factors' orders, filtered per-diagram-PAIR at 2672-2674 (`==` keeps
`combined==value`, `=`/`<=` keeps `combined<=value`, `>` keeps `combined>value`).
This filter reads ONLY `squared_orders`, NEVER `constrained_orders`. So a
single-bin isolation `NP^2==N` is enforced HERE (squared_orders route), NOT via
`constrained_orders` — that dict is the AMPLITUDE-`==` per-diagram filter
(`constrained-orders-consumption.md`), a DIFFERENT mechanism. A doc that says
"`NP^2==2` isolates the bin via `constrained_orders`" is CONFLATING the two:
`NP^2==N` never populates `constrained_orders` (4940 stores only
`squared_orders[basename]`); `constrained_orders` is populated ONLY by the bare
amplitude `NP==N`/`NP>N` (4956/4963).

## Single-run `NP^2<=N` bounds generation via the squared→amplitude injection (4994-4999)
When a squared order is given with NO amplitude order (the usual signal/bkg idiom
`generate ... NP^2<=2`), MG5 injects an amplitude bound so generation is finite:
```python
if orders=={} and squared_orders!={} and not perturbation_couplings:   # 4994 (LO-only)
    for order in squared_orders.keys():
        if squared_orders[order][0]>=0 and squared_orders[order][1]!='>':
            orders[order]=squared_orders[order][0]          # 4997  NP^2<=2 -> orders[NP]=2
        else:
            orders[order]=99                                # 4999  negative or '>' -> unbounded
```
So `NP^2<=2` sets `orders['NP']=2` (amplitude generated up to NP≤2), `NP^2<=1`
sets `orders['NP']=1`, and each parses+generates in a SINGLE tree-level run
(`<=`∈`_valid_sqso_types` 3036, no `Interpreting` rewrite for `<=`). This is what
makes the subtraction scheme work per single run:
| run | orders[NP] | |M|^2 bins kept (p=1: bin = amp+amp NP) | physics |
|---|---|---|---|
| `NP=0` (or `NP^2==0`) | 0 | {0} | σ_bkg |
| `NP^2<=1` | 1 | {0,1} | σ_bkg+σ_int |
| `NP^2<=2` | 2 | {0,1,2} | σ_bkg+σ_int+σ_sig (full) |
| `NP^2==1` | 1 (4996 `==`,val≥0 → inject) | {1} only | σ_int (SM excluded) |
| `NP^2==2` | 2 | {2} only | σ_sig (SM excluded) |
Then `σ_int = σ(NP^2<=1) − σ(NP=0)` and `σ_sig = σ(NP^2<=2) − σ(NP^2<=1)` are
SOURCE-consistent for a p=1 model (each HVV/dim-6 vertex carrying NP=1) — the
doc's claim-3 subtraction is correct under p=1. The `else: orders=99` branch (4999)
is why a NEGATIVE or `>` squared order does NOT bound the amplitude — MG cannot
know at generation time whether the amplitude is leading (comment 4988-4991), so
it leaves NP unbounded and relies purely on the post-squaring filter.

## The `NP=1` row is p-dependent: SM-only (p=2) vs full total (p=1)
The bare amplitude `NP=1` (→`orders['NP']=1`) admits every amplitude with NP≤1.
- **p=1** (HVV/SMEFTsim/dim6top, each insertion NP=1): NP≤1 admits NP∈{0,1}, so
  after squaring |M|^2 carries bins {0,1,2} = **σ_bkg+σ_int+σ_sig (the TOTAL)**.
  The common "amplitude-level `NP=1` = total (sig+bkg+int)" statement holds — correct FOR p=1.
- **p=2** (SMEFTatNLO): NP≤1 admits ONLY NP=0 (one p=2 insertion overflows the
  bound), so `NP=1` = SM-only. On `u u~ > t t~` the 3 diagrams are the SM
  QCD(1)+EW(2) tree (QED left free), NP=0 throughout — NOT interference.
So "`NP=1` = total" and "`NP=1` = background-only" are BOTH right, for different p.
The amplitude-order value that yields the full total is `NP=p` (p HVV insertions),
not literally `NP=1`.

## Convention→bin map: which `NP^2==N` selects σ_int vs σ_quad (CONVENTION-DEPENDENT)
The σ(c)=σ_SM + c·σ_int + c²·σ_quad isolation idiom. A single Wilson
insertion contributes `p` to the amplitude NP order, where `p` = the model's
NP-per-insertion convention (per-model, drift-prone: read it by counting NP units
on a Wilson-coefficient vertex in the model's `couplings.py`, or take it as GIVEN
from eft's slice). Squaring sums the two factors' NP orders (2670 above):
| |M|^2 term | amp×amp NP | combined bin | constraint |
|---|---|---|---|---|
| σ_SM   | 0 × 0 | 0   | (only `<=`, never an `==N>0`) |
| σ_int  | 0 × p | `p`   | `NP^2 == 1·p` |
| σ_quad | p × p | `2p`  | `NP^2 == 2·p` |
- **NP-per-insertion=1** (SMEFTsim, dim6top): σ_int=`NP^2==1`, σ_quad=`NP^2==2`.
- **NP-per-insertion=2** (SMEFT@NLO): σ_int=`NP^2==2`, σ_quad=`NP^2==4`, and the
  ODD bins are EMPTY when p is even — every amplitude NP is a multiple of p, so
  combined ∈ {0, p, 2p, ...}. To read p on SMEFTatNLO: open
  `models/SMEFTatNLO/couplings.py` and read a Wilson-coefficient coupling's NP
  units (e.g. `:15` `order={'NP':...,'QED':1}`) — that per-insertion NP count IS
  `p`, uniform across the NP couplings. Drop the bare value; read it fresh.
- So the SAME physics needs DIFFERENT N across models — `NP^2==2` is σ_quad under
  the SMEFTsim convention but σ_int under SMEFT@NLO. The anchored empirical
  (SMEFTsim `NP^2==2`→σ_quad, sign-flip-invariant, ratio +0.2/+0.1=4.00) is the
  per-insertion=1 column; the SMEFT@NLO `NP^2==4`→σ_quad mapping is the p=2 column.
  WHICH model uses which `p` and WHICH UFO name carries the order is eft's slice.

## The combined amplitude+squared form `NP<=1 NP^2==2` — coherent, but NOT interference
A doc (unverified) lists `NP<=1 NP^2==2` as its interference row (its table is the
p=2 pattern `==0`/`NP<=1 ==2`/`==4`/`NP<=2`). Coherence + what it selects, from
source:
- **Coherent — YES.** `NP<=1` → `orders['NP']=1` (amplitude-generation bound,
  applied at enumeration); `NP^2==2` → `squared_orders['NP']=(2,'==')` (ME diagram-
  pair filter via `pass_squared_order_constraints`). Different dicts, different
  pipeline stages, no parse conflict — both apply. Amplitudes with NP≤1 are
  generated first; the squared filter then keeps only pairs with combined NP==2.
- **What it selects = combined==2 among NP≤1 amplitudes** → requires BOTH pair
  members at NP=1 (the max allowed). It isolates `|NP=1 amplitude|²`, EXCLUDING any
  combined-2 pair that involves an NP=2 amplitude (those are never generated).
- **p=2 (SMEFTatNLO — each Wilson insertion NP=p with p even, read from
  `couplings.py`): the rider is SELF-DEFEATING → EMPTY.** `NP<=1` admits ONLY NP=0
  (no single-insertion diagram, each is NP=p≥2), so combined can only be 0, and
  `NP^2==2` matches nothing →
  NoDiagramException. Probe-consistent: cached `u u~ > t t~ NP=1 NP==1 NP^2==2` →
  NoDiagramException. The CORRECT p=2 interference is bare `NP^2==2` (combined=2 =
  SM(0)×EFT(2)); the `NP<=1` rider kills the very EFT amplitude it needs.
- **p=1 (SMEFTsim conventional, GAP — not installed): combined==2 = σ_quad, NOT
  interference.** NP≤1 admits NP∈{0,1}; combined==2 = (1)×(1) = `|single-insertion|²`
  = σ_quad, the `NP<=1` rider harmlessly excluding NP≥2 double-insertion amplitudes
  (a cleaner quadratic). For p=1 interference you want combined==1 (`NP^2==1`).
- **CONCLUSION: under neither convention is `NP<=1 NP^2==2` the interference term**
  — p=2 → empty, p=1 → σ_quad. Doc's "interference" label is source-suspect; its
  interference should be bare `NP^2==p` (`NP^2==2` for p=2, `NP^2==1` for p=1). The
  per-insertion `p` and diagram content are eft/diagram-enum's; the parse-coherence
  and combined-order rule above are in-slice.

## The c=0 discriminator: `NP^2==N` gives σ(c=0)≡0, `NP^2<=N` does not
The smoking-gun test for which constraint a run actually applied:
- `NP^2==N` (N>0): the SM×SM bin (combined=0) FAILS `0 != N` (2672), so it is
  filtered out → at c=0 only the SM bin would contribute and it is gone → matrix
  element is empty → runtime `Zero result detected`. σ(c=0) ≡ 0 EXACTLY.
- `NP^2<=N`: the SM×SM bin (combined=0) PASSES `0 <= N` (2673), so SM survives →
  σ(c=0) = σ_SM ≠ 0 (SM "leaks" into the bin pool). The c-dependent pieces are
  still capped at NP^2≤N.
This σ(c=0)=0-vs-≠0 split is governed entirely by the `==` vs `<=` branch of
`pass_squared_order_constraints` (`base_objects.py 2672-2673`). It is the only
reliable observable distinguishing the two constraints from a single run.

## The model-side `expansion_order` cap (`check_expansion_orders`) — BOUNDARY but it MUTATES this slice's dicts
`$MADGRAPH_INSTALL/madgraph/core/base_objects.py` `check_expansion_orders`
(3757-3785), called from `diagram_generation.py` 1688 / 2089 (i.e.
diagram-enumeration slice, AFTER `extract_process`):
```python
tmp = [(k,v) for (k,v) in expansion_orders.items() if 0 < v < 99]
for (k,v) in tmp:
    if k in orders:
        if v < orders[k]:
            ... warning ...; orders[k] = v
    else:
        orders[k] = v
```
- Only orders with `0 < expansion_order < 99` participate (so SMEFTatNLO's finite
  NP cap is active; QCD/QED `99` and the `-1` default are skipped). Read NP's cap
  value from `coupling_orders.py`.
- It reads `orders` AND `sq_orders` but MUTATES only `orders` (3783, 3785;
  `sq_orders` is read-only at 3770-3771, used only to decide which warning text
  fires). It never writes `squared_orders`. Effect on THIS slice's dicts: if NP
  is unconstrained it injects `orders['NP']=<NP cap>`; if the user asked for a
  higher amplitude bound it is clamped down to the cap with a warning; if a
  SQUARED order exceeds the cap it warns
  `The process with the squared coupling order (NP^2...) ... can potentially
  recieve contributions ... larger than the maximal value allowed by the model
  builder (<NP cap>). Hence, MG5_aMC sets the amplitude order for that coupling
  to be this maximal one.` and sets `orders['NP']=<NP cap>`.
- BOUNDARY: the call site and timing are diagram-enumeration territory. What is
  IN this slice: the cap reads/writes the same `orders`/`squared_orders` dicts
  `extract_process` fills, so an NP order a user sets is not the final word —
  the model's `expansion_order` can override it downstream. This is the EFT
  analogue of `default_unset_couplings` (`default-unset-couplings.md`), except
  the cap source is the model, not a set-option, and it is dim-6-truncation by
  construction (SMEFTatNLO ships truncated-at-dim-6-squared).

## `expansion_order=0` is NOT auto-excluded at LO — STRICT `0 < v`
A model order declared `expansion_order=0` (e.g. SMEFTsim's `NPprop`) is NOT
automatically excluded from an LO amplitude "unless explicitly requested" — that
claim fails against source for the LO path:
- LO `check_expansion_orders` filter is `tmp = [(k,v) ... if 0 < v < 99]`
  (`base_objects.py:3766`) — STRICT lower bound `0 < v`. A `v=0` order FAILS
  `0 < v`, is dropped from `tmp`, never enters the loop, so NO `orders[k]=0` cap
  is injected. At LO an `expansion_order=0` order gets **no amplitude cap at all**
  from this mechanism.
- The `orders[k]=0` auto-exclusion of a `v=0` (or any non-QCD/QED) order is an
  **NLO-only** behavior, and only on the **no-orders-passed** auto-detect path:
  `amcatnlo_interface.py` guards at `544` (`if not myprocdef['squared_orders']
  and not myprocdef['orders']`), then for each non-QED/QCD order (`584-585`):
  `elif o in expansion_order and expansion_order[o]<50` (`592`, **NO lower
  bound** — `0<50` is true) → `orders[o]=expansion_order[o]` (=0 for NPprop);
  `else: orders[o]=0` (`596`). Either branch zeroes it. If the user passes ANY
  order at NLO, `544` is skipped and unspecified orders instead get
  `default_unset_couplings` (`533-538`), not 0.
- CONCLUSION cached: `expansion_order=0` auto-exclusion is NLO-no-orders-passed
  behavior (`amcatnlo_interface.py:592/596`, no lower bound), NOT an LO mechanism
  (`base_objects.py:3766`, strict `0<v` skips it). The two paths diverge exactly
  at `v=0`. This is the same LO/NLO structural split as the `NP^2==N` gate below.
- GAP (not this mechanism): whether SMEFTsim's `NPprop` is nonetheless absent at
  LO by some OTHER route — WEIGHTED auto-detect settling low, or the NPprop
  vertices also carrying an `NP` power that the NP cap bounds. Those are model
  (ufo) / diagram-enum territory and unverifiable here (SMEFTsim not installed).
  Do NOT cache "NPprop excluded at LO" as established.

## CAUTION: WEIGHTED auto-detect picks QCD-ONLY for an EFT process (PROBE-CONFIRMED)
With NO order constraint, `generate u u~ > t t~` on SMEFTatNLO-NLO logs:
```
Trying coupling order WEIGHTED<=2: WEIGTHED IS NP+2*QCD+4*QED
Trying process: u u~ > t t~ NP<=2 WEIGHTED<=2 @1
1 processes with 1 diagrams generated
```
- The weight formula (probe-echoed above as `NP+2*QCD+4*QED`) is the model's
  `order_hierarchy` — read the weights from `coupling_orders.py`; see
  `split-orders-and-weighted.md`.
- Auto-detect settles on `WEIGHTED<=2`, which the QCD tree (NP=0, QCD=2 ->
  WEIGHTED=2) satisfies, so the leading contribution is QCD-ONLY and the EFT/NP
  diagrams are SILENTLY EXCLUDED. The `NP<=2` rider is the `expansion_order` cap
  above, not a user choice. To get NP at default you must ASK
  (`NP=1`, `NP^2==2`, etc.). The auto-detect VALUE/loop lives at
  `diagram_generation.py` 2014 (diagram-enumeration); what this slice owns is
  WEIGHTED as a parsed constraint NAME and the hierarchy-keyed split sort.
- Trap: a user who omits orders on an EFT model expecting "everything" gets the
  SM-only leading order. This is the EFT face of the help-text default
  "MG5 will try to determine orders to ensure maximum number of QCD vertices"
  (`order-syntax-help-reference.md` 609-610).

## `NP^2==N` is LO-accepted — distinct from the amplitude `==` LO-only gate
The squared `==` (`NP^2==N`) routes through the `^2` branch
(`madgraph_interface.py 4927-4940`) and lands ONLY in `squared_orders`, NEVER in
`constrained_orders`. The tree-only gate at `4983` (`if constrained_orders and
LoopOption != 'tree'`) keys on `constrained_orders`, so it does NOT fire for a
squared `==`. `_valid_sqso_types = ['==','<=','=','>']` (`3036`) accepts `==`, and
NO `=`→`<=` rewrite happens for `==` (`4936` rewrites only `type=='='`). So
`NP^2==N` parses verbatim at LO. PROBE-CONFIRMED: SMEFTatNLO-NLO
`generate u u~ > t t~ NP^2==2` → "Process has 13 diagrams", no warning.
Contrast: the AMPLITUDE `NP==N` (no `^2`) DOES populate `constrained_orders`
(`4956`) and IS rejected at NLO by the `4983` gate. The squared/amplitude `==`
split at the NLO boundary (squared-`==`-rejected-at-NLO) is amcatnlo/nlo-syntax's
slice; THIS slice owns only the LO-accept side and the parse routing.

Three NP^2 idioms ranked by what survives at c=0:
- `NP^2<=N`: SM (bin 0) ∈ pool → σ(c=0)=σ_SM≠0; admits all bins ≤N (interference
  AND quadratic AND SM mixed together — NOT a clean single-term isolation).
- `NP^2==N` (N>0): exactly one bin, SM excluded → σ(c=0)≡0 → single-run clean
  isolation. THE canonical LO σ_int / σ_quad isolation idiom.

## Matrix-source fingerprint (`AMPSPLITORDERS`/`SQSPLITORDERS`/`NSQAMPSO`) — scope
These live in the GENERATED Fortran, written by output/nlo-export
(`export_v4.py`/`export_fks.py`), NOT this slice. Scoped confirmation of the
linkage only: `AMPSPLITORDERS` enumerates the distinct amplitude-level split-order
tuples, `SQSPLITORDERS` the distinct |M|^2 (combined) split-order tuples,
`NSQAMPSO`/`nSqAmpSplitOrders` their count (`export_v4.py 3150-3157`). At runtime
`set_chosen_SO_index` (`export_v4.py 1171-1205`) reads THIS slice's parse-time
`process.get('squared_orders')` dict and picks which SQSPLITORDERS index(es) the
constraint selects, applying `==`/`<=`/`>` (`:1194-1198`, mirroring
`pass_squared_order_constraints`). So a single `NP^2==N` selects ONE SQSPLITORDERS
bin. The empirical `AMPSPLITORDERS=(0,1,2)` / `SQSPLITORDERS=(0,1,2,3,4)` is the
NP-per-insertion-counted-in-NP-UNITS view; the count and array contents are
output/nlo-export territory — route there for what the integers mean in the .f.
The seam THIS slice owns: the parse-time `squared_orders` dict is the INPUT.

## Per-operator coupling orders (e.g. SMEFTsim `NPclq1`) — general mechanism
The parser does NOT distinguish an umbrella order (`NP`) from a per-operator one:
both are just keys in `model_orders`. The `^2` branch validates
`basename in list(model_orders) + ['WEIGHTED']` (`madgraph_interface.py 4929`) —
ANY model-declared coupling-order name passes the identical path, so a per-operator
`NPclq1^2==2` is accepted exactly as the umbrella `NP^2==2` and stores
`squared_orders['NPclq1']=(2,'==')`, immune to other nonzero WCs (the squared-bin
filter keys on the NPclq1 order tuple alone). SMEFTsim not installed here —
the `NPclq1` name is ANCHORED (eft's slice owns the per-model order names). GENERAL
mechanism verified against SMEFTatNLO's `NP` (single umbrella order declared,
`models/SMEFTatNLO/coupling_orders.py`); a model that declares multiple order
names routes each through `4929` identically.

## Cross-references (generic mechanics, all apply to NP)
- `=`->`<=`, `==`/`>` propagation, LO-only gate: `equals-interpretation-and-strict-equality.md`.
- 2N amplitude->squared doubling: `amplitude-to-squared-doubling.md`.
- `==`/`>` as post-generation FILTER (explains NP==1 NoDiagram): `constrained-orders-consumption.md`.
- `^2` squared-order parsing, dict assembly, regex: `order-parsing-overview.md`.
- Squared-ME interference syntax + operator set (help text): `order-syntax-help-reference.md`.
- Negative `^2==-I` sub-leading selector: `negative-order-values.md`.
- WEIGHTED name-whitelist + order_hierarchy sort: `split-orders-and-weighted.md`.
- EW<->QED / aS / aEW aliases (live in SMEFTatNLO): `coupling-aliases.md`.
