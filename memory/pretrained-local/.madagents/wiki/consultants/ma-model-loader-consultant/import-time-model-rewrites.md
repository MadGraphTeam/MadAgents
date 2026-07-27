---
description: PRINCIPLE — the model after `import model` is a transformed image, not (UFO-on-disk + card literal); four load-time knobs (CMS EW-scheme, restriction+multiparticle flavour scheme, gauge Goldstones/pickle, mdl_ parameter-name prefix) silently rewrite the operative model. When a user is surprised "the model isn't what I put in", name which import-time knob caused it and tell them to `display`.
---

# Import-time model rewrites: the operative model ≠ the on-disk literal (v3.7.1)

**Principle.** What `import model <name>` leaves in `self._curr_model` is a *transformed*
image of the UFO directory and the user's param_card, not a faithful copy. Four
independent load-time mechanisms inside `do_import` / `import_ufo.import_model` /
`import_full_model` / `process_model` rewrite the operative model, each invisibly (no card
edit, no echo unless you `display`). When a user/lead is surprised that "the model isn't what
I wrote", the first move is to identify **which import-time knob** rewrote it and point at
`display parameters` / `display multiparticles` — not to trust the card or the UFO file.

This catches cases the per-mechanism pages don't individually flag: any "imported model
differs from my input" surprise routes here first, then to the owning mechanism page.

## The four rewrite knobs (each probe-confirmed)

1. **CMS activation rewrites the EW input scheme + complexifies the graph.**
   `set complex_mass_scheme True; import model sm` makes `mdl_MW` an **external**
   param (MASS[24]) and `Gf` an **internal/derived** one — the (Gf,MZ,αEW) scheme silently
   becomes (MW,MZ,αEW). Yukawa block externals are *consumed* (tied to the pole mass).
   Probe: `display parameters` showed `mdl_MW = 80.419` under `('external',)` and
   `Gf = -mdl_aEW*CMASS_mdl_MZ**2*.../...` derived. Owning page:
   `cms-activation-interior.md`. (Mechanism interior: `base_objects.py:1863` /
   `change_electroweak_mode:1779`.)

2. **The restriction + multiparticle defaults rewrite the j/p flavour scheme.**
   The file literal `p/j = g u c d s ...` (4-flavour-looking) is PROMOTED to 5-flavour
   **iff the restricted b is massless** — decided AFTER the file is read, from the
   restriction's MB. Probe: default `sm` (restrict_default b massive) → p/j stay 4-flavour, NO
   "Pass to flavour scheme" message. `sm-no_b_mass` (MB=0) → "Pass the definition of 'j' and
   'p' to 5 flavour scheme", p/j gain `b b~`. So the operative jet definition is
   restriction-dependent, not the file literal. Owning page:
   `process-model-and-multiparticle-defaults.md` (`add_default_multiparticles:5998`).

3. **Gauge selection re-imports under a different pickle and can add Goldstones.**
   `loop_qcd_qed_sm*` forces Feynman before load; a QED/EW LoopModel auto-switches to
   Feynman post-load; `set gauge Feynman` re-imports. Under Feynman the operative model
   carries Goldstones that unitary does not — a particle-SET change (gauge bit drops/keeps
   Goldstones at conversion, `import_ufo.py:1245`, and picks the gauge propagator, `:1295`),
   not just an `all`-tag change. Probe: `sm` loads 17 particles / 0 goldstones under unitary,
   19 incl. `g0`,`g+` under Feynman; `import model sm; set gauge Feynman` re-fired name-pass +
   multiparticle rebuild and `all` gained `g0 g+ g-`. Owning pages:
   `gauge-selection-and-loopmodel-autoswitch.md` (selection) and
   `gauge-dependent-model-loading.md` (converter interior).

4. **The `mdl_` prefix renames every model PARAMETER at import.** Default `import model`
   prepends `mdl_` to parameter names (`change_parameter_name_with_prefix`,
   `base_objects.py:1627`, fired from `import_full_model:440-442`) — so the operative model's
   params are `mdl_cp`, `mdl_MW`, … not the UFO's bare `cp`, `MW`. A user's `set cp 0.5`
   FAILS (the live name is `mdl_cp`); `--noprefix` suppresses it (but STILL disambiguates
   case-colliding names). The card is unaffected (keyed by lhablock+lhacode, `mdl_` stripped
   from the comment) — the divergence is names-in-CODE only. Excluded names
   (`as/mu_r/zero/aewm1/g`) keep bare. Probe: `display parameters` after default
   `SMEFTatNLO-NLO` shows `mdl_cp`/`mdl_ctG`; under `--noprefix`, bare `cp`/`ctG`. Owning page:
   `mdl-prefix-parameter-naming.md`.

## Why this is one principle, not a set of coincidences
All four fire **inside the model-load** (do_import tail / import_model / import_full_model /
process_model), all are silent (no card write), and all make the in-memory model diverge from
the on-disk UFO + the literal card. The unifying diagnostic for every "my model is wrong"
report in this slice: the divergence was decided at import, by a load-time knob, and is
visible only via `display`. The card and the UFO file are NOT the operative truth after
import. (Knobs 1-3 rewrite the PHYSICS content — scheme/flavour/particle-set; knob 4 rewrites
only the NAMES — but all four break the naive "operative model == what I put in".)

## Boundary (what this is NOT)
- NOT run-time card-value precedence (run_card/param_card values overridden at `launch`) —
  that is the lead's `config-value-lifecycle-layers` playbook. This page is the *load-time*
  analogue: the model object itself is rewritten before any run stage.
- NOT the restriction *algorithm* (restriction slice) or the UFO content itself (ufo slice).
  This page owns only "the operative model differs from the literal, and which import knob
  caused it"; the interior algebra belongs to the named owning pages / other slices.
- The instance pages are KEPT — they carry the line-cited interior each mechanism needs.
  This page is the navigational/predictive layer above them.
