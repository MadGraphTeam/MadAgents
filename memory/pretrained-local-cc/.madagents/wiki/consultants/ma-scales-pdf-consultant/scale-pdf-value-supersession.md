---
description: PRINCIPLE — a scales/PDF run-card value that IS live can still be SUPERSEDED by a different computed/coherence-driven value at a later lifecycle stage (parse-coherence -> output-freeze -> runtime-override); latest stage governs, gated by the fixed_* / lpp flags. The scales-pdf slice's instance of the lead config-value-lifecycle-layers shape; single layer-precedence routing target. Distinct from parser-vs-fortran-mismatch (values that NEVER take effect).
---

# Scales/PDF value supersession (lifecycle layering)

## Principle
A scales/PDF run-card number that the parser ACCEPTS and the Fortran HANDLES is still only a *starting point*. A later lifecycle stage can overwrite it with a DIFFERENT, live value. The value the matrix element / PDF call actually uses is set by the LATEST stage that touched it — not the card. When asked "will my scale/PDF value X be used?", name the governing stage, don't read it off the card.

**Distinct from parser-vs-fortran-mismatch.md.** That page = values that NEVER take effect (parse-rejected silent-revert / parse-accepted runtime-stop / dead-or-overridden code). THIS page = values that DO take effect but are then SUPERSEDED by a computed value. Mismatch: the number you typed is discarded. Supersession: the number you typed is replaced by a different number the code computes.

## The three supersession stages (latest governs)
1. **Parse / coherence time** (banner.py, before any Fortran):
   - lpp<->pdlabel auto-correction (pdlabel-coherence.md): `|lpp|∈{3,4}` not-lep-PDF -> `'eva'`; `|lpp|=2` not-photon-FF -> `'edff'`; `lpp=0` -> `'none'`. The pdlabel you typed is replaced before the run.
   - PDLabelBlock fills the inactive template from the active one; `'mixed'` derived from asymmetric pdlabel1/2.
   - FixedfacscaleBlock copies fixed_fac_scale to both fixed_fac_scale1/2.
2. **Output / code-gen time** (export_v4.py, frozen into the process dir; generated-pdf-assembly.md):
   - The PDF luminosity COMBINATION rule (g1*g2 vs PHOTONPDFSQUARE joint flux vs ee_comp_prod dot product) is chosen from the GENERATED process's initial states and frozen into auto_dsig.f. A run-card pdlabel change after `output` cannot move a process to the joint-flux branch — that was decided at generation.
3. **Runtime init** (Fortran; setrun.f, once per run before events):
   - **param_card αs(MZ) → PDF αs(MZ)**: for ANY PDF run (`lpp≠0`), setrun.f :130-136 reads the param_card αs then `pdfwrap` OVERWRITES `asmz` in `common/a_block/` with the chosen PDF's αs(MZ) (alphas-paths.md). The αs the matrix element uses is the PDF's, NOT the param_card's. (Gate: only when a PDF is used; no-PDF lpp=0 keeps param_card αs and forces pdlabel='none', nloop=2.)
   - `q2fact(i)=sf1**2/sf2**2` (setrun.f :84-85): the written `dsqrt_q2fact1/2` is SQUARED into `q2fact` at init — the positive seed that setclscales' :643 early-return tests (dsqrt_q2fact>0 keeps clustering away from the fac scale).
4. **Runtime, per-event** (Fortran; setscales.f / reweight.f / genps.f / ElectroweakFluxDriver.f):
   - dsc=-1: setscales.f leaves rscale=0/q2fact=0; the REAL μR/μF come from clustering geom-means in setclscales (ckkw-clustering-scale-resolution.md). The written `scale`/`dsqrt_q2fact` are ignored for the not-fixed beams.
   - dsc=1-4: set_fac_scale DEFERS q2factorization to the ren-scale (`tempscale**2`) for not-fixed beams (setscales.f :182-186) — dsqrt_q2factN is NOT used unless fixed.
   - EVA μF floor: a μF below MV is silently auto-RAISED to mu2min every event (eva-flux-driver-internals.md :138-141).
   - beam mass: mass_ion overrides the lpp-derived beam mass; ebeam below the beam mass is auto-raised to it (beam-mass-stot.md :668-671).

## The governing boundary — the fixed_* / lpp gates
Supersession is NOT unconditional. Every runtime override is GATED, and the gate is what pins a written value through all later stages:
- **`fixed_ren_scale=.true.`** pins `scale` (set_ren_scale skipped, scale-runtime-eval.md).
- **`fixed_fac_scaleN=.true.`** pins `dsqrt_q2factN`: EVERY q2factorization overwrite in setscales.f (:136-137, :146-147, :184-185) and setclscales (:1128) is guarded `if(.not.fixed_fac_scaleN)`. A fixed beam keeps its written μF through dsc=-1, dsc=1-4, and clustering alike.
- **`lpp=9`** (PLUGIN) exempts the ebeam<mass floor (beam-mass-stot.md :670).
- pdlabel auto-correct fires ONLY when the typed value is outside the allowed set for that lpp (pdlabel-coherence.md); a coherent pdlabel is left untouched.

So the operating rule: **a value is superseded UNLESS its fixed_*/lpp gate pins it.** To make a scale literally the value the ME uses, set the matching `fixed_*` flag; otherwise expect the latest-stage computed value.

## Cases beyond the named instances
The principle catches any future scales/PDF knob with a later-stage computation gated by a fixed/coherence flag — e.g. a new dynamical_scale_choice branch, a new beam type's mass assignment, a new lep-density auto-correction — not just the six instance pages. The diagnostic ("which stage last wrote this value, and is its gate set?") is general; the instance list is illustrative, not exhaustive.

## Caution
- This is the scales-pdf slice's contribution to the lead's `config-value-lifecycle-layers` cross-subtree playbook. When the lead routes a "I set scale/PDF X but the run did Y" question here, this is the layer-precedence page; the instance pages carry the per-mechanism detail.
- Runtime stderr-print supersessions (EVA μF auto-raise message, dsc=10 stop) are RUNTIME predictions — the dsc=10 trap is probe-verified (parser-vs-fortran-mismatch.md); the EVA μF auto-raise stderr print is read from source, NOT probe-verified here.
