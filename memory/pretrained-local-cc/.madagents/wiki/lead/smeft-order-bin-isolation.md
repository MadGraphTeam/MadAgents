---
description: You want ONE polynomial power of a Wilson coefficient. The linear (interference), the quadratic, or the whole sum.
---

# SMEFT polynomial-order bin isolation — σ_SM / σ_int / σ_quad

This class spans several SMEFT scenarios — LO σ_quad of O_lq^(1), LO σ inclusive of O_tG, NLO σ inclusive with cQq83, NLO σ_int of O_tG. All turn on the polynomial decomposition

  σ(c) = σ_SM + c·σ_int + c²·σ_quad

and on getting MG5 to compute the **one piece the user asked for**.

## When it applies (regime trigger)

Surface keywords: "linear in c_X" / "interference" / "the σ_int piece"; "quadratic" / "pure dim-6-squared" / "c² piece" / "σ_quad"; "inclusive SM + EFT"; any process line carrying `NP=`, `NP^2==`, `NP^2<=`, `DIM6=`, or a per-operator order like `NPctG^2==`; "which NP^2 bin", "why is my σ independent of the sign of c", "why did my Wilson-coefficient edit do nothing", "isolate the BSM contribution".

This is the **silent-fail twin** of `coupling-vertex-viability.md` ("a clean run is not evidence the coupling is viable"). There the operator may be zeroed by the benchmark; here the operator is present but the wrong **squared-order bin** is selected. Diagnostic in both: σ-signature, never "it ran."

## The two axes that drive the whole class

**Axis 1 — convention (the bin LABEL is not portable).** Each UFO assigns an NP-per-insertion weight `p`. The squared-amplitude bins are NP^2 ∈ {0, p, 2p}:

| piece | bin (general) | SMEFT@NLO p=2 | SMEFTsim / dim6top p=1 |
|---|---|---|---|
| σ_SM | NP^2==0 | `NP^2==0` | `NP^2==0` |
| σ_int (linear) | NP^2==p | `NP^2==2` | `NP^2==1` |
| σ_quad (quadratic) | NP^2==2p | `NP^2==4` | `NP^2==2` |
| inclusive sum | NP^2<=2p (or amp `NP=p`) | `NP=2` / `NP^2<=4` | `NP=1` / `NP^2<=2` |

Source-confirmed (eft/coupling-order): SMEFT@NLO assigns one NP-per-insertion `p` uniformly — read `expansion_order` at `coupling_orders.py:9-11`, and every NP-carrying coupling in `couplings.py` shares that single even `'NP':p` (grep it). Squared = sum of two amplitude powers (`base_objects.py:2670-2671`), EVEN+EVEN, so with an even `p` the **odd NP^2 bins are identically empty** — `NP^2==1` on SMEFT@NLO selects nothing (→ SM only or empty). dim6top uses the order **name** `DIM6` (+`FCNC`), not `NP`, with its own `p` (read its `coupling_orders.py`) — `NP^2==N` on dim6top errors at parse (wrong order name). The two most common silent fails are *porting a bin number across conventions*: `NP^2==2` means σ_quad on SMEFTsim but σ_int on SMEFT@NLO (sign-flips); `NP^2==4` means σ_quad on SMEFT@NLO but an empty bin on SMEFTsim (→ `Zero result`).
Owner pages: `../consultants/ma-eft-consultant/smeftatnlo-np-bin-selection-and-odd-empty.md`; `../consultants/ma-coupling-order-consultant/smeft-np-power-counting.md` (now convention-gated, supersedes its prior universal "NP^2==2 = interference"); `../consultants/ma-eft-consultant/dim6top-fcnc-second-eft-order.md`.

**Axis 2 — LO accepts `==`, NLO rejects it (single-run vs forced multi-run).**
- **LO**: `NP^2==N` is accepted (the LO-only gate `madgraph_interface.py:4983` keys on `constrained_orders`, which a *squared* `==` never enters) → **single-run isolation** of one bin. σ_quad in one launch.
- **NLO, has-Born** (`[QCD]`): `NP^2==N` (any non-`<=` squared operator) is **rejected** — `amcatnlo_interface.py:542` (predicate `:541`), verbatim `The squared-order constraints passed are not '<='`. The predicate is on the operator STRING, not the value, and fires at parse before diagram generation. Only `NP^2<=N` rides with `[QCD]`. So at NLO you **cannot select σ_int directly** → extract by **subtraction** across two runs (antisymmetric `[σ(+c)−σ(−c)]/2` cancels σ_SM and all even-in-c terms exactly; SM-baseline is noisier).
- **NLO, loop-induced** (`[noborn=QCD]`): the `:541` reject is **reached only on the amcatnlo has-Born path** — the line itself is a `sqorders_types != '<='` test (NOT a `has_born`-field test); a has-Born `[QCD]` process reaches it, but an **explicit `[noborn=]`** process is routed away *before* it by `master_interface.py:200-236` to `create_loop_induced` (`madgraph_interface.py:5357-5420`), which carries **NO squared-order check**. So a loop-induced EFT signal (gg→HH-type, gg→Zh) **accepts single-run `NP^2==N`** and isolates σ_int / σ_quad in one launch — the LO idiom transfers here, unlike has-Born `[QCD]`. The gate is keyed on the **bracket type** (`[QCD]` vs `[noborn=]`), not on physical loop-inducedness; the routing seam spans nlo-syntax (parse) → amcatnlo (`:541` reject) vs coupling-order + madloop (loop-induced accept). Owner pages: nlo-syntax `np-order-with-bracket-smeftatnlo.md`; amcatnlo `do-add-nlo-order-revalidation.md`.
Owner pages: coupling-order `smeft-np-power-counting.md` (LO accept); `../consultants/ma-amcatnlo-consultant/do-add-nlo-order-revalidation.md` (NLO reject + the firing order); `../consultants/ma-nlo-syntax-consultant/np-order-with-bracket-smeftatnlo.md` (how `NP^2<=N` rides the bracket; `NP` cannot go inside `[...]`).

**Axis 2b — the complete `NP^2==N` accept/reject surface map (five entry points, not two).** The `==` operator is parsed at several distinct places; whether a squared order survives depends entirely on which parser the process line reaches:

| surface | `NP^2==N`? | source | note |
|---|---|---|---|
| tree non-chain `generate` | **ACCEPT** | `madgraph_interface.py:4927-4940` (`^2`→`squared_orders`) | not gated by the `:4983` `constrained_orders` gate |
| reweight `change process` (tree-mode) | **ACCEPT** | `reweight_interface.py:1759-1776` (routes to tree `generate`) | ONLY without `[...]`; adding `[QCD]` diverts to `get_LO_definition_from_NLO` which **strips** the marker. A tree-mode reweight of NLO events is a back-door bin isolation the direct NLO path forbids |
| `[noborn=]` loop-induced | **ACCEPT** | `create_loop_induced` (pre-`:541`) | Axis 2 above |
| NLO has-Born `[QCD]` | **REJECT** | `amcatnlo_interface.py:541-542` (`sqorders_types!='<='` on amcatnlo path) | Axis 2 above |
| decay chain — MadSpin decay OR directly-typed `generate` chain (`p p > t t~, t > ...`) | **REJECT** | `madgraph_interface.py:3301-3304` `decays_have_squared_orders` (`base_objects.py:3576-3582`) | MadSpin has NO own check (`interface_madspin.py` only warns on `=`); it always splices a comma-chain → hits this shared guard. Same guard rejects a hand-typed decay-chain. Owner: madspin `madspin-decay-chain-grammar.md` |

Take-away for routing a bin-isolation ask: a squared order is legal ONLY in a **bracket-free, comma-free** process line (or a tree-mode reweight of that form). The moment the spec adds a decay chain or an NLO bracket, `NP^2==N` is unavailable — fall back to subtraction (has-Born NLO) or to isolating the bin at generation and decaying separately.

## Dispatch sequence

1. **eft FIRST** — it sets everything downstream. Read the chosen UFO's NP-per-insertion `p` (→ bin labels), which restrict-card variant keeps the target operator alive, the operator's block/lhacode, and the QED-order on the operator's couplings (the QED=0 trap, below). Don't compose any order constraint before this — the order NAME and `p` are per-model.
2. **bin constraint** — branch on LO vs NLO:
   - LO → **coupling-order**: `NP^2==2p` single-run for σ_quad; `NP^2==p` for σ_int; `NP^2<=2p` (or amplitude `NP=p`) inclusive.
   - NLO (`[QCD]`) → **nlo-syntax + amcatnlo**: `NP=p [QCD]` inclusive, or `NP=p NP^2<=p [QCD]` + antisymmetric subtraction for σ_int. `==` is rejected.
3. **restriction** — confirm the restrict card doesn't strip the operator (the removed≠small precondition; see below). Distinct dispatch because the *mechanism* (parse-time order WIPE, operator pruning) is restriction's, not eft's catalog.
4. **param-card** — target WC nonzero; **zero ALL other WCs** (restrict cards ship scrambled-nonzero placeholders, not 0); keep Λ.
5. **regime knobs** (only if the prompt asks): kinematic-cuts (`mmll` for a high-mass tail), scales-pdf (NLO PDF), phase-space (`sde_strategy=2`).
6. **physics** — why the regime (energy-growing contact amplitude → high-mass tail), what σ_int/σ_quad mean physically, EFT-validity of a quad-only truncation.

## Anticipated traps (catalog — pointers, not restated mechanism)

**A': proposing `NP^2==N` for a has-Born NLO process is a known failure mode.** The command *parses* at LO (so "it ran" is not evidence), but at NLO **with a Born** (`[QCD]`) it gets a hard parser rejection. The trap: the LO `NP^2==N` idiom is correct at LO but is a red herring at has-Born NLO — it does not transfer, because the `:541` reject fires (per Axis 2). For a has-Born `[QCD]` EFT process, always use the ±c subtraction recipe, never `NP^2==N`. **Exception:** an *explicit* `[noborn=]` loop-induced process bypasses the reject (Axis 2, NLO-loop-induced bullet) and accepts single-run `NP^2==N` — do not reflexively push subtraction there.

**A. Bin / convention silent fails (the deepest surface; σ-feedback is usually closed by "I'll run it myself"):**
- *Convention-mismatched bin number* — `NP^2==2` under SMEFT@NLO gives σ_int (sign-flips) not σ_quad; `NP^2==4` under SMEFTsim gives an empty bin (`Zero result`). eft `smeftatnlo-np-bin-selection-and-odd-empty.md`.
- *`NP^2<=N` instead of `==N`* — admits the whole polynomial (SM+int+quad), not the isolated bin; tell is σ(c=0)≠0. coupling-order `smeft-np-power-counting.md`.
- *`NP=N` (amplitude order) with no `^2`* — admits all squared bins; not isolated. coupling-order.
- *`NP=1` on SMEFT@NLO* — admits ZERO EFT amplitudes (even-`p` convention), silent SM-only; diagram count drops to the SM-only subset (for gg→tt̄). eft.
- *`NP^2==N` at NLO* — parser-rejected (hard fail, recipe won't run). amcatnlo `do-add-nlo-order-revalidation.md`.
- *single-run report at NLO with `NP=2 [QCD]`* — reports σ_SM+c·σ_int+c²·σ_quad as "σ_int" (~100× off); needs subtraction. amcatnlo.

**B. Operator-stripped-before-bin-selection (removed≠small — instance of `removed-coupling-not-small.md`):**
- *bare `import model SMEFTatNLO`* → restrict_default zeros all WCs → the NP coupling order is **WIPED** (`import_ufo.py:2478-2486`: `coupling_orders=None`, `order_hierarchy={}`, `expansion_order=None`) → `NP^2==N` fails at parse "model order NP^2 not valid". restriction `restriction-and-coupling-orders.md`; eft `smeftatnlo-default-restriction-trap.md`.
- *`SMEFTatNLO-NLO_no4q`* → zeros **every** DIM64F op including the light-quark-coupling `cQq83` (the diff is exactly the DIM64F lines → σ-difference `0.000000`); `set cQq83 1.0` is then inert, σ≈σ_SM_NLO silently. restriction `smeft-restrict-operator-selection.md`; eft `smeftatnlo-restrict-card-taxonomy.md` (DIM64F is 4-fermion all-quark, cQq83 is 3rd-gen-Q × light-gen-q — not just "4-heavy-quark").
- *`SMEFTatNLO-LO` + `[QCD]`* → LO restrict lacks UV/R2 counterterms → MadLoop pole-cancellation hard fail. eft / nlo-model.
- *wrong-sector UFO for light-quark DY* — dim6top AND SMEFT@NLO semileptonic 4f ops (`cQlM1`) couple only third-gen-quark currents (b b̄ ℓℓ, t t̄ νν), never u/d → `p p > l+ l-` (4-flavor p) emits NoDiagramException; only SMEFTsim's `clq1` is flavor-universal. eft.

**C. Param-card contamination:**
- *"leave other WCs at default"* — the generated card carries every WC at its scrambled-nonzero restrict-card placeholder (written verbatim), so σ(c_target=0)≠0 from contamination. Must explicitly zero each non-target WC. param-card `smeft-wilson-coefficient-blocks.md`; restriction (placeholder origin = distinct-nonzero-float anti-merge idiom).
- *zeroing Λ* — Λ is the EFT scale (block DIM6 lhacode 1), not a WC; zeroing → c/Λ²→∞ NaN. (Note `cQq83`/`cQlM1` ship a tiny non-unity UFO default, not 1.0 — only `ctG` defaults to unity; read `parameters.py`. Immaterial since the operative card carries the restrict placeholder.)

**D. Regime / runtime knobs:**
- *QED=0 trap (two faces)* — (i) at NLO, omitting `QED=0` leaves QCD^2 unconstrained → defaulted to 0 (`amcatnlo_interface.py:618-619`) → no QCD Born → switches to **loop-induced** gg→tt̄ (a different quantity; the No-Born→loop-induced switch is fks/master-interface `master_interface.py:232`). (ii) on SMEFTsim, `g g > t t~ QED=0` silently kills ALL ctG vertices because ctGRe-couplings carry QED≥1 (the O_tG Higgs-vev factor) — anchored; dim6top's ctG coupling has no QED key (`couplings.py:2910-2922`) so it survives QED=0 (source-confirmed). eft; amcatnlo.
- *no `mmll` for a high-mass-tail ask* — σ in the wrong kinematic regime (Z-pole-dominated, ~2.3× the tail value). `mmll` is an SFOS-pair invariant-mass low-cut (`setcuts.f:396-399`, `cuts.f:480-499`); a cut on `ptl`/`etal`/`drll` is the wrong variable (silent bias). kinematic-cuts.
- *`sde_strategy`* — needed (`=2`) only when an **amplitude-level** filter strips the SM (NP=0) amplitudes from the matrix file (`NP==1`, or `NP=2 NP^2==4` on SMEFT@NLO) AND the process is pure-lepton/proton — banner **actively forces DY back to `sde_strategy=1`** (`banner.py:4998-5012`), exactly the crashing strategy (`All amp2 are zero but not the total matrix-element`, STOP 1). A *squared* filter (`NP^2==2`) leaves NP=0 amplitudes present → no crash → no fix needed. phase-space `single-diagram-enhancement-amp2-weight.md`.
- *NLO PDF* — a `[QCD]` process writes run_card from the **NLO template**, whose default `pdlabel` is already an NLO PDF set (read `RunCardNLO`) — so it is NLO-PDF-consistent out of the box; the trap is only an explicit *downgrade* to an LO PDF, and there is NO hard ME-order↔PDF-order guard (silent). To use a specific lhapdf set you must set BOTH `pdlabel=lhapdf` AND `lhaid` (lhaid alone is inert). scales-pdf `lo-vs-nlo-pdf-default.md`.

## Return-interpretation hints

- **"It parsed" / "MG5 emitted no warning" answers parse-validity, NOT bin-correctness.** A consultant return saying "the constraint is accepted" is the wrong question — re-frame to "which physical piece does THIS UFO's `p` put in the bin I wrote." The σ-feedback channel is usually closed (setup-only), so you cannot iterate empirically; the convention must come from source.
- **σ can be degenerate across several traps** — whenever the EFT piece is a small fraction of the SM σ (common at inclusive NLO), the no4q / NP=1 / NP^2<=2 traps land within MC error of each other and of the SM, so σ alone cannot distinguish them (how small the fraction is is process-specific — never assume). Route the verdict to the **structural fingerprint**, not σ: GC-code count in `matrix*_orig.f`, JAMP order classes in `born.f` (two classes NP=0+NP=2 = correct bin, one class = silent fail), diagram count, NSQAMPSO/orders.inc `BORN_ORDERS`. *(The operator→GC-code map is per model/process — e.g. GC_35↔cQq83, GC_358/360↔ctG on one SMEFTatNLO setup, illustrative only — read it per process, never reuse.)* These are output/nlo-export's emission; ask coupling-order/eft to predict them, ask `/mg-probe` to read them.
- **σ-vs-sign-of-c is the single cleanest live discriminator**: pure σ_quad is EVEN in c (σ(+c)=σ(−c)); pure σ_int is ODD (σ(+c)=−σ(−c)); σ(c=0)≡0 under `==N` (N>0) vs ≠0 under `<=N`. If asked to verify a candidate at runtime, `/mg-probe` two opposite-sign and one zero WC value.
- **A consultant declining + redirecting is high-value** — e.g. phase-space owns the amp2-array side but defers "which filter strips which amplitude" to coupling-order/eft; amcatnlo owns the `==`-reject but defers the No-Born→loop-induced verdict to fks/madloop. Follow the redirect.

## Siblings
- `coupling-vertex-viability.md` — "clean run ≠ viable operator"; here clean run ≠ correct bin. Same "diagnose by σ-signature/structure, not by exit-0" discipline.
- `removed-coupling-not-small.md` — the restrict-card-strips-operator precondition (trap family B) is a direct instance.
- `eft-smeft-fanout.md` — the general EFT slice-router; this page is the deep dive on the order-bin sub-question.
- `derived-quantity-staleness.md` — same family of "MG5 uses what you gave it verbatim, no consistency check, no warning."
