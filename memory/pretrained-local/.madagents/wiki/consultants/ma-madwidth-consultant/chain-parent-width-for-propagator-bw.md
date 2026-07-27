---
description: Decay-chain angle — how a chain-decayed parent gets the width its propagator BW needs; per-pid independent compute_widths loop; the named-param-vs-'zero' subtlety that gates BW config allocation; auto-left-at-0.0 → zero-width BW.
---

# Chain-parent width for the propagator's Breit-Wigner (v3.7.1)

The decay-chain user's question: when you `generate p p > t t~, t > b w+`, the `t` (and in a cascade `w+`) is an s-channel propagator that needs a width for its Breit-Wigner. Where does that width come from, and what happens if it was never computed? This page owns the **width-production half** of that connection and names the **consumption boundary** (diagram-gen / helas slices) precisely. The compute_widths engine internals are on the other ten pages; this is the chain-specific framing.

## The engine has NO notion of "chain" — it computes one width per requested pid
`do_decay_diagram` (madgraph/interface/madgraph_interface.py:10189) loops `for part_nb, pid in enumerate(pids):` — **each requested pid is enumerated independently** as its own decaying particle. There is no cascade awareness: a 2-level chain `t > b w+, w+ > c s~` needs BOTH the `t` and `w+` widths, and each is computed as a standalone particle (or via `compute_widths all`). The chain SYNTAX in `generate` does not feed the width engine; the engine only sees the pid list you (or the runtime auto-scan) hand it.
- Per-pid skip: `if part.get('width').lower() == 'zero': continue` (10191) — a particle whose width ATTRIBUTE is the literal string `'zero'` is skipped (no channels enumerated). See the subtlety below: an `auto`-flagged parent is NOT `'zero'`.

## The named-param-vs-'zero' subtlety (the non-obvious bit)
At generation/consumption time `part.get('width')` returns the width **parameter NAME** (e.g. `WT` / `mdl_WT`), not the numeric value (models/import_ufo.py:1279 sets the width attribute to the param name). It equals the literal `'ZERO'` ONLY if restriction pruned that width to the zero-parameter (`fix_parameter_values`, import_ufo.py:2990-2991: `if particle['width'] in zero_parameters: particle['width'] = 'ZERO'`).
- An `auto`-flagged width is collected by `modify_autowidth` and given the `log10(2N)` placeholder during restriction (NON-zero — see autowidth-restriction-callback page), so it is NOT in `zero_parameters`. Its width attribute keeps its named parameter (e.g. `WT`), NOT `'ZERO'`.
- **Consequence:** an `auto`-flagged chain parent's width attribute is `!= 'zero'`, so it is NOT skipped at do_decay_diagram:10191, AND its propagator IS allocated a Breit-Wigner config slot at the consumer (below). But the NUMERIC value driving that BW is whatever the card holds — `0.0` if `auto` was never computed (load-time stand-in, model_reader.py:186; see width-stand-ins-vs-written-width). So you get a BW slot with a **zero width** = a numerically degenerate / non-resonant propagator until `compute_widths` populates the card.

## Where the parent width is CONSUMED (boundary — NOT my slice)
The width the engine writes is read by two generation-side mechanisms, both keyed on the width ATTRIBUTE string `!= 'zero'`:
1. **BW config count** (madgraph/core/base_objects.py:2775-2787, `get_num_configs`): `num_props = len([s-channel ids where model.get_particle(i).get('width').lower() != 'zero'])`; returns `2**num_props`. Each non-`'zero'`-width s-channel propagator DOUBLES the integration-channel count (one channel treats it on-shell BW, the mirror off-shell). A chain parent with width attribute `'ZERO'` contributes NO factor of 2 — no BW spread for that leg. (Owned by the diagram-generation slice.)
2. **On-shell resonance split** (madgraph/core/helas_objects.py:213): `if s_pdg and (part.get('width').lower() == 'zero' or leg.onshell == False): s_pdg = 0` — a `'zero'`-width or off-shell s-channel is NOT written as a distinct resonance in the event file. (Owned by the helas slice.)

These are NOT my slice — I own the production of the width the card carries; the BW-config-count and resonance-split CONSUMPTION live in diagram-generation / helas. Route propagator-BW / config-count / `decayBW.inc` questions there. What my slice establishes: the card's `auto` parent gets a real number only after `compute_widths` (LO survey or `--nlo`/SMWidth) runs; until then the attribute is a named param (not `'zero'`) but the value is 0.0.

## Runtime auto-scan vs REPL — who triggers the chain parent's compute
- **Bare MG5 REPL** `compute_widths` requires ≥1 explicit particle (check_compute_widths, madgraph_interface.py:1796-1799); it does NOT auto-detect chain parents or AUTO-flagged widths. You must name the parent pids or use `compute_widths all`.
- **Runtime (MadEvent/aMC) and MadSpin** wrappers DO auto-scan the param_card for `DECAY <pid> auto[@NLO]` (common_run_interface.py:7301 regex) and compute those — so a chain parent flagged `auto` in the card gets recomputed at launch without an explicit command. (The launch-time auto-recompute trigger itself is the launch slice; I own only the regex→compute dispatch.) See compute-widths-flow page for the entry-point table.

## What is OUT of this slice (boundary checks)
- `--recompute_width=never|first_time|always|auto` (madgraph_interface.py:543, 4259; process_checks.py:3680) is the `do_check` CMS/gauge-check width-recompute control, NOT a chain-decay-parent width source. It lives entirely in the `check` command (process-checks slice). Confirmed: every `recompute_width` reference is under `do_check`/`process_checks.py`, none in process generation or the width engine.
- `change_mass_to_complex_scheme` width-zero check (base_objects.py:1901-1910) is the complex-mass-scheme conversion (model/CMS slice), not chain-parent width production.

## Cautions
- A chain parent left as `auto` (= 0.0 at load) generated/launched WITHOUT a prior compute_widths gives a zero-width BW for that propagator — kinematically pathological (on-shell pole un-regulated). The runtime auto-scan normally prevents this at launch; a bare-REPL output-then-manual-run can hit it.
- "The parent's width is `'ZERO'`" (attribute is the literal zero-parameter, e.g. restriction pruned it, or the model declares it massless/stable) is a DIFFERENT state from "the parent's `auto` width is 0.0 (uncomputed)": the first skips the engine AND drops the BW config slot; the second keeps both but with value 0.0. Don't conflate the string `'zero'` attribute with a numeric 0.0 value.
- The engine computes pids independently — a cascade chain needs every parent pid requested; missing one leaves that level's parent at its card value.

## Boundaries
- Compute engine internals (entry points, two-stage FR/survey, write-back): compute-widths-flow.
- The three `auto` stand-ins and the restriction restore loop: autowidth-restriction-callback; the four-stand-in classification: width-stand-ins-vs-written-width.
- BW config count (`2^num_props`), on-shell resonance split, `decayBW.inc`: diagram-generation / helas slices (NOT mine).
- Launch-time auto-recompute trigger: launch slice (I own only the regex→do_compute_widths dispatch).
- `--recompute_width` CMS-check option: process-checks slice.
