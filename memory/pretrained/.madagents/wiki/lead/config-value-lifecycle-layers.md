---
description: A card value you set is not what the run behaved as if it had, or you must know whether an edit reaches the ME.
---

# Config-value lifecycle layers — "the written card is not the enforced value"

## When it applies

Any question of the shape:
- "I set `X` in the run_card / param_card but the run did `Y` / ignored it."
- "Does my hand-edited card value actually survive to the matrix element?"
- Surprise that cut values, factorization/renormalization scales, matching params, or masses came out different from what the card shows.
- "Why did the generated default card already carry `X` — I didn't set it?"

This is one of the most common diagnostic classes a user brings, and the naive answer ("the card says X, so the run used X") is wrong often enough that it has its own playbook.

## The dispatch-level principle (cross-subtree, confirmed across ≥8 slices)

A single config value is touched at **multiple distinct lifecycle stages**, and the value that actually governs the run is set by the **latest-firing stage for that value** — which is frequently *not* what the written card shows:

1. **Creation / defaulting** — `create_default_for_process` and friends write process-driven defaults into the card at `output`/card-generation time (cuts hidden for absent particle classes, matching auto-enabled for multi-jet, maxjetflavor from beams). *Visible in the card.*
2. **Parse / validate** — `check_validity` (banner.py) re-checks and silently repairs the user's current values at write/launch time (scheme-consistency, auto-disables, reverts of rejected enum values). *Visible in the card, but reverts can be silent.*
3. **Runtime** — Fortran (`setcuts.f`, `treatcards`→`param_card.inc`, per-event) and the integrator apply the operative value. **This layer leaves no card trace.** A runtime override (e.g. `ptj` forced to `xqcut` for a matched sample) governs the run regardless of the card.
4. **Downstream-tool bridge** — a handoff stage (e.g. `setup_Pythia8RunAndCard`) owned by a *different tool* can re-gate or even **abort** a card that passed stage 2. The canonical case: CKKW both-on (`ktdurham>0 AND ptlund>0`) **passes `RunCardLO.check_validity`** but raises `InvalidCmd` at the PY8-setup stage (`@4500`). So "my run_card validated cleanly but the matching setting still aborted / got rewritten" is a stage-4 symptom — the abort is deferred past validity to the bridge. This is a distinct failure shape from the runtime override (stage 3): the bridge can *reject*, not just silently override.

Corollary the user most often trips on: **the written run_card records only layers 1–2; a layer-3 override is invisible.** And for param_card: **only *external* parameters reach the Fortran matrix element** (via `param_card.inc`); internal/dependent params are recomputed Fortran-side and never read from the card — a stale dependent value is inert at the ME but still leaks to the LHE banner / Pythia / MadSpin.

## Dispatch sequence

1. **Identify the value's owning slice** (use the routing index — cuts → kinematic-cuts; scales/PDF → scales-pdf; masses/widths/Wilson coeffs → param-card; matching knobs → matching/amcatnlo; BW → bw-window).
2. **Dispatch that consultant's layer-precedence page** and ask specifically: *which stage fires last for this value, and does the run_card record it?* Do not accept "the card shows X" as the answer — that is layer 1–2.
3. If the question is "does the value reach the Fortran ME at all," that is specifically a **param-card** (external-vs-internal) or **kinematic-cuts** (runtime setcuts.f) question.

## Per-slice instance pages (pointers — facts live in the consultant subtrees)

- **kinematic-cuts** → `../consultants/ma-kinematic-cuts-consultant/cut-value-layer-precedence.md` — 3 layers; runtime `setcuts.f` forces `ptj=xqcut`/`mmjj` for matched samples regardless of the card value (probe-confirmed, logged only in `G*/log.txt`).
- **param-card** → `../consultants/ma-param-card-consultant/` (override-stages + the "only external params reach Fortran" correction) — internal/dependent params recomputed Fortran-side; `launch -f` skips the edit-time `update dependent` recompute. **Load-time instance** → `../consultants/ma-param-card-consultant/restriction-pruned-external-is-dropped.md` — a *restriction-zeroed* external is DROPPED from both the editable card (lhacode gaps) AND `ident_card.dat`, so a later user hand-edit of that line is **silently inert** (no ident match → never read). This is the early-stage-removes-the-slot shape: it is not "value overwritten" but "slot deleted," so the fix is re-`output` with a keeping restriction, never a card edit. Probe-confirmed model-independent (SMEFTatNLO Wilson coeffs + `sm-no_b_mass` ymb/MB); the EFT face is "my Wilson coefficient line isn't in the card / didn't take effect."
- **matching** → `../consultants/ma-matching-consultant/matching-config-lifecycle.md` — **three** moments: auto-detect (Moment 1, at `output`) → `check_validity` (Moment 2, at launch) → **the Pythia8 bridge `setup_Pythia8RunAndCard` (Moment 3)**, which owns all CKKW cut-selection/Merging:TMS/MLM-qCut and can **abort** a card that passed Moment 2 (CKKW both-on → `InvalidCmd @4500`). Structural decisions from `proc_characteristic` are Moment-1-only and defeatable by a later hand-edit (re-adding `ickkw=1` to a HEFT-limitation card survives). This is the slice that surfaced the stage-4 downstream-bridge shape.
- **restriction** (load-time analogue) → `../consultants/ma-restriction-consultant/cms-restriction-sequencing.md` — under complex-mass-scheme the restrict card is read 2–3 times; the *latest* read governs pruning because `set_parameters_and_couplings` (`model_reader.py`) **rebuilds the parameter/coupling dicts wholesale on every call** (not patch-in-place), so the early `complex_mass_scheme=False` pre-read seeds only the massive/massless classification and is overwritten. Same "latest call wins" shape at model-load time; route CMS "which value drove pruning" here.
- **amcatnlo** → `../consultants/ma-amcatnlo-consultant/fxfx-ickkw3-lifecycle.md` — FxFx (`ickkw==3`) enforced/repaired at **5** distinct stages, each with a different reaction.
- **bw-window** → `../consultants/ma-bw-window-consultant/bw-param-layer-map.md` — `bwcutoff` lives only in the window/classification layer (never touches the integration jacobian); `small_width_treatment` spans both layers with different roles.
- **scales-pdf** → `../consultants/ma-scales-pdf-consultant/scale-pdf-value-supersession.md` (the slice's dedicated layer-precedence landing page) — a live scale/PDF card value is a starting point superseded by a later computed value (parse-coherence → output-freeze → runtime override), latest governs, **gated by `fixed_ren/fac_scale` and `lpp`**: every `q2fact` overwrite in `setscales.f`/`setclscales` is guarded `if(.not.fixed_*_scaleN)`, so a hand-set scale only sticks when its `fixed_*` flag is on. Complement: `../consultants/ma-scales-pdf-consultant/parser-vs-fortran-mismatch.md` covers the *never-takes-effect* axis (parse-accepted/Fortran-unhandled → runtime `stop` for `dynamical_scale_choice=10`; parse-rejected → **silent revert to previous value** on file-read — a typo'd/cross-pasted value runs with the wrong PDF, no error).
- **nlo-syntax** → `../consultants/ma-nlo-syntax-consultant/nlo-mode-lifecycle-stages.md` — the same shape applied to the `NLO_mode`/`has_born` field: a 4-stage lifecycle (routing-classify in the Switcher → parse-remap in `extract_process` → store → command-override by `do_check`/`create_loop_induced`); no single stage is authoritative and stages 1–2 disagree *by name*. Future override sites are stage-4 additions invisible to stages 1–3. Route "what does `[noborn=]`/`[virt=]` actually set, and when" here.
- **model-loader** (load-time analogue, not run-card) → `../consultants/ma-model-loader-consultant/import-time-model-rewrites.md` — the operative model after `import model` is a transformed image, **not** (UFO-on-disk + card literal): gauge, complex-mass-scheme (silently flips the EW input scheme — `mdl_MW` external, `Gf` derived, probe-confirmed), and restriction+multiparticle-defaults silently rewrite it. Route "my model/params aren't what I wrote" surprises here, then to the owning mechanism page, and tell the user to `display`.

## Return-interpretation hints

- When a consultant return says "the card shows X," that is the creation/parse layer — ask the follow-up about the runtime/latest layer before telling the user the run used X.
- "Silent revert" and "forced at runtime" are the two failure shapes that leave no card evidence — treat any "but the card clearly says X" user report as a layer-3 suspect.
- Do **not** assume a downstream tool (Pythia / MadSpin / LHE banner) saw the same value the ME used — param-card splits the two (externals → `param_card.inc` for the ME; full card → banner/downstream).

## Related lead pages
- `the routing pages` — `## Cross-slice seams` carries the cuts-two-layer and BW-three-slice seams this playbook generalizes.
