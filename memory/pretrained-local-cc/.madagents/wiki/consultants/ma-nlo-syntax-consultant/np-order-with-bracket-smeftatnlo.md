---
description: NP (or any perturbative_expansion=0 coupling order) and a [...] bracket — NP is NOT bracket-perturbable, coexists as an ordinary <= amplitude constraint, suppresses the amcatnlo perturbation_couplings overwrite, and is never order-bumped; SMEFTatNLO / NP-at-NLO intersection. ALSO the NP^2<=N squared-order CAP path — parsed on the extract_process path as a (value,type) tuple into sqorders_types (5334), the <=-only NLO restriction (C6a amcatnlo:542) is the LO↔NLO asymmetry — NP^2==N parser-accepted (valid sqso type) but rejected at NLO; NP^2=N silently rewritten to <=. The C6a squared-order <=-only reject is MODEL-AGNOSTIC (fires on any order Xxx^2==N/>N on any [...] process incl. loop-induced g g > 4l QCD^2==2 [QCD]); squared-order signal/bkg/interference isolation at NLO must use cumulative <= runs + subtraction, never a single == bin.
---

# NP coupling order with a [...] bracket (SMEFTatNLO / NP-at-NLO)

How an NP-style coupling order intersects the `[...]` perturbation bracket in extract_process.
v3.7.1 / $MADGRAPH_INSTALL (SMEFTatNLO-NLO).
Companion to bracket-parse-and-loopoption-mapping (the bracket parse) and
amcatnlo-do_add-perturbation-couplings-overwrite (the stage-5 overwrite/bump that this NP case
interacts with).

## The model split that drives everything (SMEFTatNLO coupling_orders.py:9-20)
```
NP  = CouplingOrder(name='NP',  expansion_order=2,  hierarchy=1)            # NO perturbative_expansion -> defaults 0
QCD = CouplingOrder(name='QCD', expansion_order=99, hierarchy=2, perturbative_expansion=1)
QED = CouplingOrder(name='QED', expansion_order=99, hierarchy=4)            # NO perturbative_expansion -> 0
```
The UFO importer (`models/import_ufo.py:501-502`) keeps an order in `perturbation_couplings`
ONLY if `order.perturbative_expansion > 0` (consumer's own predicate — see lead dead-code-liveness;
`=1` literal grep would also work here but `>0` is the test). So in SMEFTatNLO:
- `perturbation_couplings = ['QCD']` (ONLY QCD has perturbative_expansion>0).
- `coupling_orders = ['NP','QCD','QED']` (all three).

**Probe-confirmed (`import model SMEFTatNLO-NLO`):**
`m.get('perturbation_couplings') == ['QCD']`, `sorted(coupling_orders) == ['NP','QCD','QED']`.

Consequence: **NP is a Born-side amplitude-order constraint only — it is NOT bracket-perturbable.**
QED is ALSO not bracket-perturbable in this model (no perturbative_expansion). Only QCD can sit in `[...]`.

## What parses, what fails (parse-probed, extract_process exit)
| input | result |
|---|---|
| `t t~ > t t~ NP=1 [QCD]` | OK — NLO_mode=all, has_born=True, pert=`['QCD']`, orders=`{'NP':1}` |
| `t t~ > t t~ NP<=1 [QCD]` | OK — same; `NP=1` and `NP<=1` are equivalent (amplitude upper bound) |
| `t t~ > t t~ NP=2 [QCD]` | OK — orders=`{'NP':2}` |
| `t t~ > t t~ [QCD]` (no NP) | OK — orders=`{}` |
| `t t~ > t t~ [NP]` | **rejected** — end-to-end `generate` shows `validate_model` "does not allow to generate loop corrections of type ['NP']" (loop_interface:325-326), then raises `InvalidCmd("The model ... cannot handle loop processes")` (355-356). Calling `extract_process` DIRECTLY instead gives interface:5286 "Perturbation order NP is not among the perturbation orders allowed for by the loop model." — but the live generate flow never reaches 5286 (see item 1 below). |
| `t t~ > t t~ [QED]` | **rejected** — same `validate_model` message for QED (`['QED']`), probe-confirmed. |
| `t t~ > t t~ [QCD] NP==1` | **InvalidCmd**: "Amplitude order constraints (for not LO processes) can only be of type <=, not '=='." (constrained-order guard, interface:4983-4985) |

Three distinct guards fire on the NP×bracket cases:
1. **`[NP]` / `[QED]` rejected — WHICH guard fires depends on the path.**
   The bracket pertOrders are validated against `model['perturbation_couplings']` (=`['QCD']`), NOT
   against `coupling_orders`; NP/QED are in coupling_orders but not perturbation_couplings, so both
   fail (also NOT coupling-aliased — same asymmetry as `[EW]` failing while `EW=2` constraints work;
   bracket-parse page). TWO guards can reject them and the LIVE-path one is NOT 5286:
   - **End-to-end `generate [NP]`/`[QED]`** (probe-confirmed): the Switcher routes the bare `[NP]`
     bracket as nlo_mode=`'all'` -> aMC@NLO `do_add`, which calls `validate_model(proc_type[1],
     coupling_type=proc_type[2])` (amcatnlo_interface:513) BEFORE `extract_process` (525).
     `validate_model` (loop_interface:297-356) tests `any(coupl not in
     _curr_model['perturbation_couplings'] for coupl in coupling_type)` (312-313) and, for a non-`sm`/
     non-`loop_sm` model like SMEFTatNLO, logs "The current model ... does not allow to generate loop
     corrections of type ['NP']." (325-326) then raises `InvalidCmd("The model ... cannot handle loop
     processes")` (354-356). **This is the user-visible rejection — interface:5286 is never reached.**
   - **`extract_process` called in ISOLATION** (e.g. directly, bypassing the Switcher/aMC@NLO
     routing): THEN the 5286 loop-model perturbation-order check fires with "Perturbation order NP is
     not among the perturbation orders allowed for by the loop model." Probe-confirmed both ways.
     The "[NP] -> 5286 message" holds only for a DIRECT extract_process
     call; the live `generate` path is shadowed by validate_model (presence-vs-liveness — the 5286
     guard exists but is unreached on the normal path). Route "what does the user see" to
     validate_model; route "what does extract_process enforce in isolation" to 5286. This is the
     general inner-vs-outer-guard shadowing — full treatment + probe table (incl. `[EW]`, `[bogus=]`,
     sm-auto-upgrade) on `extract-process-guards-shadowed-by-outer-routing.md`.
2. **`NP==1` / `NP>1` rejected with a bracket** — the constrained-order guard (interface:4983-4985):
   `if constrained_orders and LoopOption != 'tree'` raises. `==` and `>` are the `constrained_orders`
   types; only `<=` survives for a non-tree LoopOption. So with `[QCD]` present you may write `NP=1`
   or `NP<=1` (treated as an amplitude upper bound, NOT a `constrained_order`) but NOT `NP==1`/`NP>1`.
   This is the NP-specific manifestation of the generic `[QCD] QED==2` rejection.
3. **`NP=1 [QCD]` itself is fine** — NP is an ordinary amplitude order constraint that lives in
   `orders`; the bracket independently perturbs QCD. No interaction at the parse boundary.

## NP suppresses the amcatnlo perturbation_couplings overwrite (generate-probed)
The amcatnlo do_add overwrite (amcatnlo_interface.py:672-673) fires only when
`not myprocdef['orders'] and nlo_mixed_expansion`. An explicit `NP=` constraint makes
`myprocdef['orders']` NON-empty, so the overwrite is SUPPRESSED — `perturbation_couplings` stays
`['QCD']` instead of being replaced by the model's full `coupling_orders` `['NP','QCD','QED']`.
This is the same suppression mechanism as `QED=0` (amcatnlo page) — ANY explicit amplitude order does it.

**Generate-probed (`generate t t~ > t t~ NP=1 [QCD]`):**
`pert=['QCD']`, `orders={'NP':1, 'QED':99, 'QCD':100}`, `sq={'NP':2, 'QED':198, 'QCD':200}`.
- `pert=['QCD']` — overwrite NOT fired (orders non-empty due to NP=1).
- **Bare `t t~ > t t~ [QCD]` (no order constraint) does NOT reach the overwrite in SMEFTatNLO — it
  ERRORS first.** With `orders` AND `squared_orders` both empty, do_add runs the auto-order
  determination (amcatnlo_interface.py:545-561): `find_optimal_process_orders` gives `WEIGHTED=2`,
  then `get_qed_qcd_orders_from_weighted` returns `qed=-1, qcd=3`, and the `qed<0` test at :558-561
  raises `MadGraph5Error: Automatic process-order determination lead to negative constraints: QED:
  -1, QCD: 3` (probe-confirmed; surfaced as an `IndexError` in the error formatter, but the
  operative raise is the negative-constraints guard at :559). So in this EFT model you MUST supply an
  explicit order constraint (e.g. `NP=1`) with the bracket. The `[ all = NP QCD QED ]`-style overwrite
  display is a single-/QCD+QED-friendly model behavior (loop_sm — amcatnlo-overwrite page), NOT
  SMEFTatNLO; do not attribute it to bare `[QCD]` here.
- `QCD` order 99->100, squared 198->200: the +1 / +2 NLO bump (635-655) on the PERTURBED order.
- **NP is NEVER bumped.** The bump loop (amcatnlo_interface.py:635) iterates only over
  `perturbation_couplings` (=`['QCD']`); NP is not in it, so the NP constraint is preserved exactly
  as typed. `orders['NP']=1` stays 1; `squared_orders['NP']=2` is just the 2×1 guess from the
  squared-orders default (631-632, "No squared orders... will be guessed"), not a bump.
- The `QED=99` / `sq QED=198` entries are the default-unset/guess fills, not user input.

`generate t t~ > t t~ NP=2 QED=0 [QCD]` -> `orders={'QED':0,'NP':2,'QCD':100}`,
`sq={'QED':0,'NP':4,'QCD':200}`: confirms NP=2 preserved (sq NP=4=2×2), QED=0 preserved (sq 0),
QCD bumped to 100/200. Overwrite suppressed.

## Why `QED=0` matters at NLO — and the correction to "omitting it zeroes QCD → loop-induced"
A canonical SMEFTatNLO NLO form is `generate p p > t t~ QCD=2 QED=0 NP=2 [QCD]` (illustrative — the
`QCD=2`/`NP=2` integers are the tt̄ Born QCD power / chosen insertion power; derive per process). What `QED=0`
actually does, from the order-defaulting source path (amcatnlo_interface.py):
- When `myprocdef['orders']` is NON-empty but not every model coupling order appears, the missing
  ones are filled to `default_unset_couplings` (fill loop 533-537, `myprocdef['orders'][o] =
  self.options['default_unset_couplings']` at 536, warning 537). **`default_unset_couplings` ships an
  unbounded "infinity" sentinel — NOT 0** — read its default fresh at madgraph_interface.py:3112
  (the `... means infinity` comment sits at that registration line).
- So `p p > t t~ NP=2 [QCD]` (QED omitted, but NP specified → orders non-empty) fills BOTH QED and
  QCD to **the unbounded sentinel, not 0**. Unbounded QED ADMITS the EW Born diagrams (qq̄→γ*/Z→tt̄),
  so the "NLO QCD" sample is contaminated by EW Born instead of being pure QCD-tt̄. That is the real
  effect of omitting `QED=0`: **EW-Born contamination, NOT loop-inducedness.** QCD is filled to the
  unbounded sentinel, never 0, so the qq̄/gg QCD Born is always present — the process does NOT
  silently become loop-induced.
- **The "omitting QED=0 zeroes QCD → loop-induced" phrasing is only true if `default_unset_couplings`
  has been overridden to 0** (`set default_unset_couplings 0`; the example at madgraph_interface.py:8185),
  a NON-default user action. Under that override an unspecified QCD fills to 0, the QCD Born vanishes,
  and the process can degrade to loop-induced/empty. With the shipped (unbounded) default it cannot.
- Bare `p p > t t~ [QCD]` (NO orders at all → `orders`+`squared_orders` both empty) does NOT reach
  the fill loop — it hits the auto-order block (545-561) which yields `qed=-1` and ERRORS at the
  negative-constraint guard (559), as documented above. So in SMEFTatNLO you cannot omit orders
  entirely, and `QED=0` + an explicit `QCD=N` are both load-bearing (QED=0 excludes EW Born; the
  explicit `QCD=N` pins the QCD Born power — N = the count of QCD vertices in the Born tree, DERIVE
  per process, never a fixed integer; `NP=N` is the EFT-insertion power, chosen per analysis).
- Whether the resulting Born topology is exactly "qq̄+gg QCD only" (QED=0) vs "QCD + EW mixture"
  (QED=99) is a generated-diagram outcome → PROBE-CANDIDATE (diagram count / Born content of
  `p p > t t~ QCD=2 NP=2 [QCD]` with vs without `QED=0`, SMEFTatNLO-NLO). The SOURCE mechanism
  (fill-to-sentinel, not 0) is decisive that it is contamination, not loop-inducedness, under shipped defaults.

## The `NP^2<=N` squared-order CAP alongside `[QCD]` — the LO↔NLO asymmetry
A SMEFT σ_int subtraction (`p p > t t~ QCD<=2 QED=0 NP=2 NP^2<=2 [QCD]`) carries a SQUARED-order
constraint `NP^2<=2` in addition to the amplitude orders. Two distinct constraint kinds, two
distinct guards — and the squared-order kind has a `<=`-ONLY restriction at NLO that does NOT exist
at LO. This is the recurring trap.

**The squared-order is parsed on MY path (extract_process), as a `(value,type)` tuple.**
The order/squared-order parse loop (madgraph_interface.py:4883-4885 regex, loop 4914-4940):
- a token ending in `^2` (4927) is a squared-order; `basename=name[:-2]` (4928), validated against
  `model_orders+['WEIGHTED']` (4929-4932).
- its `type` (the operator `<=`/`==`/`=`/`>`) is checked against `_valid_sqso_types =
  ['==','<=','=','>']` (3036, guard 4933-4935 "Type of squared order constraint ... not supported").
  **So at the parse level `NP^2==2` is ACCEPTED** (`==` is a valid sqso type) — and `NP^2=2` is
  ACCEPTED too but SILENTLY REWRITTEN to `<=` with `logger.warning("Interpreting 'NP^2=2' as
  'NP^2<=2'")` (4936-4939). The tuple `(value,type)` lands in `squared_orders[basename]` (4940).
- At the ProcessDefinition store (5329-5341): the tuple is split — `sqorders_values=
  {k:v[0]}` (5329) and **`sqorders_types={k:v[1]}` (5334)** — both stored on the procdef
  (5340-5341). `NP^2<=2` -> `sqorders_values={'NP':2}`, `sqorders_types={'NP':'<='}`.

**The `<=`-only NLO rejection fires LATER, in amcatnlo do_add (C6a, NOT my slice's raise site).**
amcatnlo_interface.py:541-542 (premise — amcatnlo's slice; verified the LINE):
```python
if myprocdef['sqorders_types'] and any([v != '<=' for v in myprocdef['sqorders_types'].values()]):
    raise MadGraph5Error("The squared-order constraints passed are not '<='.\n Other kind of
                          squared-order constraints are not supported at NLO")
```
The guard reads the `sqorders_types` field MY parse populated (5334). So `NP^2==2` parses fine
through extract_process (type `==` is valid sqso), is STORED with `sqorders_types={'NP':'=='}`, then
**C6a:542 rejects it at NLO** because `'==' != '<='`. `NP^2=2` parses but the 4936-4939 rewrite turns
it into `<=` FIRST, so it SURVIVES C6a (the `=` form does NOT reach C6a as `=` — it is `<=` by then).
The error text matches 542 verbatim (the operative `if` is 541, raise 542).

**Model-AGNOSTIC — not SMEFT-specific (loop-induced `g g > 4l` etc.).** The C6a guard (541) reads
`myprocdef['sqorders_types']` with NO reference to the model or the order name — it fires on ANY
non-`<=` squared order (`Xxx^2==N`, `Xxx^2>N`, for ANY order Xxx) on ANY process routed through
aMC@NLO `do_add` (i.e. anything carrying a `[...]` bracket, incl. loop-induced `[QCD]`). Concretely
`generate g g > e+ e- mu+ mu- QCD^2==2 [QCD]` (a loop-induced `gg>4l` signal/interference isolation
by squared coupling order) hits 541 and is rejected at NLO for the SAME reason `NP^2==2` is — and
`do_add`'s 541 runs BEFORE amplitude generation, so the `==` reject precedes any NoBornException /
loop-induced classification.

**SCOPE CORRECTION (do not over-generalize "any loop-induced"):** C6a:541 fires only on brackets
that ROUTE THROUGH aMC@NLO `do_add` — i.e. the has-born-TYPED brackets (`[QCD]`, `[real=]`,
`[LOonly=]`; Switcher master:212-217). A process that is *physically* loop-induced but typed `[QCD]`
(like `gg>4l`) still routes to aMC@NLO and hits 541 BEFORE FKS finds no Born, so it IS rejected.
But an EXPLICITLY-typed `[noborn=QCD]` bracket routes Switcher master:218-225 STRAIGHT to
`create_loop_induced`, bypassing aMC@NLO `do_add` entirely — C6a:541 is NEVER reached, and `^2==` /
`^2>` squared orders ARE accepted there. Probe: `g g > z z QED^2==4 [noborn=QCD]` OK vs the same on
`[QCD]` rejected. So "model-agnostic, fires on ANY [...]" is correct for aMC@NLO-routed brackets only;
the explicit `[noborn=]` keyword is the exception. Full treatment + probes on
create-loop-induced-and-noborn-override page. The SMEFTatNLO/NP framing above is one instance; the load-bearing fact
(only `<=` squared-order constraints survive at NLO; `==`/`>` rejected at 541-542; `=` pre-rewritten
to `<=` at 4936-4939 so it survives) is model-independent. So squared-order signal/bkg/interference
separation at NLO/loop-induced MUST use cumulative `<=` runs + subtraction, never a single `==` bin.

**The LO↔NLO asymmetry (the trap):** at LO (`LoopOption=='tree'`, no bracket) the C6a guard is never
reached (it lives in the aMC@NLO do_add path) — a tree-level `p p > t t~ NP^2==2` ACCEPTS the `==`
squared-order and computes the pure NP^2-quadratic bin (coupling-order slice owns the LO accept). Add
`[QCD]` and the SAME `NP^2==2` is rejected by C6a:542. So `NP^2==N` (and any non-`<=` sqso) is
LO-only; at NLO you may use ONLY `NP^2<=N` (a CAP). This is the squared-order analog of the
amplitude-order `==`/`>` rejection (4983 guard, above) — but a DIFFERENT guard (542 vs 4983) on a
DIFFERENT field (sqorders_types vs constrained_orders).

**Bin selection (HYPOTHESIS — runtime KEEP_ORDER masking is nlo-export slice; not probed here):**
- `NP=2 [QCD]` (no NP^2 cap): NP is a Born amplitude `<=` bound; NP^2 ∈ {0,2,4} are ALL admitted
  (SM², SM×NP-interference, NP²-quadratic) — inclusive.
- `NP=2 NP^2<=2 [QCD]`: the cap masks NP^2=4, leaving NP^2 ∈ {0,2} = SM² + interference (σ_int
  via subtraction). The runtime KEEP_ORDER/orders.inc emission that enforces the cap per-bin is
  nlo-export slice. From MY parse view: the cap arrives as `sqorders_values={'NP':2}` +
  `sqorders_types={'NP':'<='}` on the procdef; that is what FEEDS the bookkeeping.

## Net behavior for NP-at-NLO process specification
- To perturb QCD at NLO with an NP power: `generate ... NP=N [QCD]`. NP rides as a Born-side
  amplitude upper bound; the bracket perturbs QCD. has_born stays True (full NLO-QCD: born+virt+
  real+CT), NLO_mode='all'.
- You CANNOT put NP in the bracket; NP is not perturbatively expanded in this model.
- Specifying NP explicitly suppresses the perturbation_couplings overwrite, so the displayed bracket
  stays `[ all = QCD ]` rather than expanding to all coupling_orders. (The unconstrained alternative
  does NOT simply expand here — bare `[QCD]` errors at the negative-constraint auto-order guard; see
  above. The explicit order is required, not merely tidier.)
- For mixed QCD+QED NLO you'd need the bracket to perturb both, but in SMEFTatNLO QED is not
  perturbable (perturbative_expansion=0) — `[QED]` and `[QCD QED]` both fail the 5286 loop-model
  guard. Only QCD-perturbed NLO is available from the bracket in this model.

## Boundaries
- WHY NP is born-only (the EFT power-counting / `expansion_order=2` truncation, NP^2 squared-order
  interference selection, R2/UV for NP loops) — nlo-model / eft slice.
- The amp_split per-coupling-order bookkeeping (`amp_split_orders.inc`, `amp_split_size`) is built in
  `iolibs/export_fks.py` (grep-located: all amp_split refs live there) from the procdef's
  squared_orders — nlo-export/fks slice. From the parser's view, the squared_orders the bracket+NP
  produce (`{'NP':2,'QCD':200,...}`) are what FEED that bookkeeping, but the split-array construction
  is not my slice.
- The `perturbative_expansion`->`perturbation_couplings` derivation (import_ufo.py:501) is nlo-model
  slice; cited here only to explain which orders the bracket can take.
- `=` vs `<=` vs `==` amplitude-constraint SYNTAX semantics are coupling-order slice; I own only
  that the `==`/`>` forms are rejected with a bracket (4983 guard) while `=`/`<=` survive.
