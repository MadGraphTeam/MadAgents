---
description: How UFO model files DECLARE decay widths — particle.width (a Param ref stored as the param NAME string), external width Parameter with lhablock='DECAY'/lhacode=[pdg], ZERO convention, decays.py Decay objects (partial_widths dict of analytic per-channel expressions) loaded into the Model only under decay=True.
---

# How the UFO files declare decay widths (sm, v3.7.1)

Width information is declared across THREE UFO files, with three distinct mechanisms. The loaded Model carries the *total* width as a parameter-name reference; the *partial* (analytic) widths are an optional decoration consumed only on a decay-load. All paths below are `$MADGRAPH_INSTALL/models/sm/` unless noted.

## 1. `particles.py` — the `width` attribute is a Param REFERENCE, not a number
Each `Particle(...)` declaration has a required `width` arg (`object_library.py:69` `require_args` lists `'width'`). Its value is a reference into `parameters.py`:
- `particles.py:30` `width = Param.WZ` (the Z), `:44` `Param.WW` (W+), `:234` `Param.WT` (top), `:298` `Param.WH` (Higgs), `:376` `Param.WTau` (tau).
- `particles.py:16,60,74,...` `width = Param.ZERO` — every stable/treated-stable particle (all light fermions, gluon, photon, neutrinos) points at the single internal `ZERO` parameter.

**Loader storage (the non-obvious bit):** `import_ufo.py:1279-1280`:
```python
elif key in ['mass','width']:
    particle.set(key, str(value))
```
The Param object's `str()` is its `name`, so the loaded Model stores `particle['width'] == 'WZ'` / `'ZERO'` — the parameter NAME string, NOT the numeric value. Same rule as `mass`. The number lives only on the Parameter object (below); the particle holds a symbolic pointer.

## 2. `parameters.py` — the external width Parameter carries the DECAY lhablock
The width values are external `Parameter` objects, `parameters.py:189-227`:
```python
WZ = Parameter(name='WZ', nature='external', type='real', value=2.44140351,
               lhablock='DECAY', lhacode=[23])
```
- Five external widths: `WZ`[23], `WW`[24], `WT`[6], `WH`[25], `WTau`[15] — read values at `parameters.py:189-227`. lhacode is `[pdg]`.
- **`lhablock='DECAY'`** (not a normal `DECAY` *block-name* in a BLOCK; the LHA `DECAY` statement) — this is what makes the width land in the param_card's `DECAY <pdg> <value>` lines rather than a `Block` section. lhacode `[pdg]` is the single PDG code. (How that becomes the param_card DECAY block is param-card slice; the UFO just *declares* the lhablock tag.)
- `ZERO` (`parameters.py:14-18`) is `nature='internal'`, `value='0.0'` — a single shared internal constant, no lhablock/lhacode. A `Param.ZERO` width is therefore NOT writable in any card; it is hard-zero.

So a particle's total width = look up `particle['width']` name in the parameter table; if `'ZERO'` it is the internal 0, otherwise it is a card-settable external DECAY entry.

## 3. `decays.py` (OPTIONAL) — analytic PARTIAL widths per channel
`decays.py` declares `Decay(...)` objects (`object_library.py:247-258`):
```python
class Decay(UFOBaseClass):
    require_args = ['particle','partial_widths']
    def __init__(self, particle, partial_widths, **opt):
        ...
        all_decays.append(self)
        particle.partial_widths = partial_widths   # l.258 — mutates the Particle at import
```
- **`partial_widths` is a dict keyed by a FINAL-STATE PAIR of Particle objects** → an analytic width-expression STRING. e.g. `Decay_H` (`decays.py:11`) keys `(P.W__minus__,P.W__plus__)`, `(P.Z,P.Z)`, `(P.b,P.b__tilde__)`, ... → strings like `(((3*ee**4*vev**2)/(4.*sw**4)+...)*cmath.sqrt(MH**4-4*MH**2*MW**2))/(16.*cmath.pi*abs(MH)**3)`. These are the tree-level 1→2 partial-width formulas in terms of model params (couplings, masses, `cmath`).
- The keys are 2-body only (sm ships `Decay_H/Z/W+/W-/t/c`; light particles have no Decay object).
- **Import side-effect:** merely importing `decays.py` (as a Python module) appends to `all_decays` AND sets `.partial_widths` on the Particle objects (l.258). This happens to the *UFO* Particle objects, independent of the MG5 loader.

## Loader consumption of partial_widths — GATED on `decay=True`
`import_ufo.py:426-438`:
```python
if decay and hasattr(ufo_model,'all_decays') and ufo_model.all_decays:
    for ufo_part in ufo_model.all_particles:
        p = model['particles'].find_name(name)
        if hasattr(ufo_part,'partial_widths'):
            p.partial_widths = ufo_part.partial_widths
        elif p and not hasattr(p,'partial_widths'):
            p.partial_widths = {}
```
- Copied onto the MG5 Particle ONLY when `import_full_model(decay=True)`. A plain `import model sm` leaves `partial_widths` unset/`{}` on the MG5 Model even though `decays.py` exists. (See `ufo-loader-per-declaration-consumption.md` CONDITIONAL rule, l.426-438 row.)
- `import_ufo.py:1312-1313` explicitly EXCLUDES `partial_widths` from the per-property set loop — it is never set via the normal particle-attribute path, only via this decay block.
- The pickle key includes `decay`, so a decay-load and a non-decay-load use different pickle files (`py3_dec_model.pkl` vs `py3_model.pkl` — both present in `models/sm/`).

## Physics encoding (what decays.py means)
- Each `partial_widths` string is the analytic Γ(particle → final-state-pair) at tree level, in model parameters. The total width parameter (WZ etc.) is the *numeric* sum a user/card supplies; the partial_widths are the *symbolic* breakdown used to compute branching fractions / a recomputed total.
- `ZERO`-width convention = the particle is treated as stable (no DECAY card entry, no Breit-Wigner width). Named-width convention = card-settable total, optionally backed by an analytic decays.py breakdown.

## Boundary (NOT this slice)
- **WHO consumes the analytic partial_widths at runtime** (madwidth recompute vs. trust the card value) — madwidth slice. From source I can only say the loader *attaches* the dict under `decay=True`; whether the analytic value is then USED or RECOMPUTED is not settled in `import_ufo.py`. (Probe-candidate, listed below.)
- **The param_card DECAY-block lifecycle** (how lhablock='DECAY' becomes a `DECAY <pdg> <value>` line, card overrides) — param-card slice.
- **What PHYSICAL width value to use** — physics slice. The width numbers here are the UFO's shipped defaults only (read at the coordinate).
- **Restriction-stage width handling** — `import_ufo.py:2990-3001` rewrites a particle `width` to `'ZERO'` when its param is in `zero_parameters` (e.g. `restrict_no_widths.dat`). That is the restriction slice; in slice I only note the rewrite exists.

## Probe-candidates
- (expensive) Whether `decays.py` analytic partial_widths are actually CONSUMED for a width number at generation/launch time, vs. recomputed by madwidth from the diagrams, vs. ignored in favor of the card DECAY value. The loader only attaches the dict; the consumer is out of slice (madwidth). Resolving needs a runtime trace of a `compute_widths` / `--with_decay` run.
