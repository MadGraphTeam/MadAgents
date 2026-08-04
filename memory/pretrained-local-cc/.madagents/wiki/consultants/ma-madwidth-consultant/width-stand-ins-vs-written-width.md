---
description: PRINCIPLE — four non-physical width stand-ins (load 0.0, restriction log10(2N), compute-time 1, apx_decaywidth estimate) occupy width slots at distinct lifecycle stages and NONE is ever written; only two values are real written widths (FR 2-body analytic, survey _results.dat). Classify any mid-pipeline width number before quoting it.
---

# Width stand-ins vs. the written width (v3.7.1)

Generalizes two instance pages — `autowidth-restriction-callback` (the three string-replacement placeholders) and `apx-decaywidth-is-a-gate-not-a-width` (the apx estimate) — into one classification: across the whole auto-width pipeline, several DIFFERENT non-physical numbers occupy a particle's "width" slot at different stages, and NONE of them is the value that lands in the operative param_card. Only TWO values are ever written. This page owns the classification; the instance pages own each stand-in's mechanism.

## The principle
A `DECAY <pid> auto` flag passes through ~four stages before a number is written. At each stage the literal `auto` (or the running apx estimate) is replaced by a non-physical stand-in whose ONLY job is to let the next stage's machinery run. The physical width is computed once, at the very end, by the MadEvent survey — everything before it is scaffolding. So: **a width-shaped number you observe mid-pipeline (in a loaded model, a restricted card, an integration-scaffold card, or a verbose enumeration dump) is almost certainly a stand-in, not the width.**

## The four non-physical stand-ins (none ever written)
| Stand-in | Site | Stage | Why it exists | Fate |
|---|---|---|---|---|
| `'0.0'` (string→float) | `models/model_reader.py:186` | normal model load (no restriction callback) | a particle with `auto` width loads as zero-width | overwritten when `compute_widths` runs |
| `log10(2*N)` | `models/import_ufo.py:2388` (`modify_autowidth`) | model restriction | nonzero, distinct-per-pid so coupling/param merging doesn't divide-by-zero or merge auto particles as "identical zero" | restored to the literal `'auto'` string by the restore loop (`import_ufo.py:2467-2475`) |
| `1` (float) | `madgraph/interface/madgraph_interface.py:9851-9852` (LO) and `:10040-10041` (`compute_widths_SMWidth`, NLO) | compute-widths time | a unit dummy so the integration scaffold / Fortran reads a numeric width | survey (LO) or smwidth (NLO) result overwrites it |
| `apx_decaywidth` | `mg5decay/decay_objects.py:4479` (`get_apx_decaywidth`) | channel enumeration | crude analytic estimate driving the body_decay depth gate + min_br prune | NEVER written — structurally absent from the write-back data path (it is a field on the `mg5decay` Channel, not on the survey `_results.dat`) |

## The TWO values that ARE written
| Written width | Site | When |
|---|---|---|
| FR 2-body analytic | `madgraph_interface.py:9914` (`value` into `decay_info`) → `update_width_in_param_card` (`:9917-9918`) | model ships `partial_widths` and `body_decay` reaches the 2-body stage; the analytic LO 2-body formula evaluated at scale=mass IS a real partial width (subject to the colored-state QCD-scale zeroing floor, `:9909-9912`, read the literal there) |
| Survey `_results.dat` | `madevent_interface.py:2983-2984`: `result = float(results.strip().split(' ')[0])`, divided by grouping factor `nb_output` (`:2982`) → `collect_decay_widths` → `update_width_in_param_card` | N>2-body (and 2-body when no `partial_widths`); the MadEvent numerical integral |

Both written values flow through the SAME chokepoint: `update_width_in_param_card` (`madevent_interface.py:2998`), which strips existing DECAY blocks and rewrites total + BR sub-lines. (NLO/SMWidth is a third write site — `compute_widths_SMWidth` writes `param.value=width` directly, total only, no BR table — see `nlo-smwidth-width-path`.)

## What this catches beyond the instances
- **"My restricted param_card shows a width like 0.30103 (=log10(2)) — is that physical?"** No — it's the restriction placeholder `log10(2N)` for N=1; the restore loop *should* have turned it back to `auto`, so seeing a `log10`-looking number means you're inspecting the model mid-restriction, not the final card. (Placeholder page covers the mechanism; this page connects it to "is it my width?")
- **"My card shows width = 1.0 for an auto particle — did compute_widths give it width 1?"** No — `1` is the compute-time integration dummy; if it survived, the survey/smwidth write-back did not complete. Neither instance page frames `1.0` as a diagnostic of an incomplete run.
- **"A loaded model reports width 0 for a particle I flagged auto."** Expected — load-time `0.0`; run `compute_widths` to populate it.
- **"The verbose enumeration log prints `(width = 1.2e-03)` per channel — is that my partial width?"** No — `apx_decaywidth` estimate (gate page). 
- The cross-cutting completeness bound: the apx estimate, though never written, GATES which channels get surveyed (min_br prune on the estimate), so it indirectly bounds which partial widths get a written value at all.
- **"My card width looks physical but the run gave wrong kinematics after I changed a mass."** A FIFTH failure mode, distinct from the four stand-ins: a STALE but real written width. It is a genuine survey/FR value — just computed at OLD masses/couplings. Editing `Block mass` does NOT recompute the `DECAY` width and emits NO warning (width is `nature='external'`, untouched by `update_dependent`); MG5 uses the stale number verbatim. The four stand-ins are non-physical-and-never-written; this one is physical-but-for-the-wrong-inputs. Regenerate via `compute_widths`/`DECAY <pid> Auto`/`set WH Auto` — see `compute-widths-flow` ("Stale width after a MASS edit").

## Boundary
- Each stand-in's full mechanism: `autowidth-restriction-callback` (the three string placeholders) and `apx-decaywidth-is-a-gate-not-a-width` + `apx-matrixelement-estimator` (the apx estimate). This page owns only the classification "scaffold vs written."
- The survey integration that produces the written width, and the two-stage FR/MadEvent split: `compute-widths-flow`.
- The NLO/SMWidth write path (a separate third write site): `nlo-smwidth-width-path`.
- param_card SLHA format of the written `DECAY` line: param-card slice (not ours).
