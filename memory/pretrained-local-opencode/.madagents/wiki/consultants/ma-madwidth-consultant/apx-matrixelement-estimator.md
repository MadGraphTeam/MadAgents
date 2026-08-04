---
description: The approximate matrix-element-square estimator (get_apx_matrixelement_sq / get_apx_fnrule / color_multiplicity_def) behind apx_decaywidth — the analytic guess MadGraph uses ONLY to decide how many body-levels to enumerate, not the physical width.
---

# Approximate matrix-element-square estimator (v3.7.1)

All citations `mg5decay/decay_objects.py`. This is the physics *inside* the `matrixelement_sq` factor that channel-enumeration-bodydecay names but does not unpack. The estimator is a crude analytic stand-in for a real |M|^2 — fast, never integrated — used to compute `apx_decaywidth` and thus drive the body_decay precision-loop stop criterion. It is NOT the width MadEvent reports.

## get_apx_decaywidth (4479)
`Gamma = get_apx_matrixelement_sq(model) * get_apx_psarea(model) / (2*|M|)` (4489-4491), M = antiparticle mass of the initial id. Memoized via `apx_width_calculated` flag (4485-4486) — computed once per channel.

## get_apx_matrixelement_sq (4064) — the energy-flow model
Builds `apx_m` as a PRODUCT of per-leg and per-vertex factors. Key construction:
- `avg_q = (|M| - sum(final_mass_list)) / n_final` (4080): the kinetic energy budget |M|-Σm_final is split EQUALLY across final legs. Each final leg carries `mass + avg_q` as its energy q.
- `q_dict` (4081) threads energy up the diagram: each vertex's mother-leg energy = sum of its product-leg energies (4119-4120); internal propagator legs reuse the stored energy (4109).
- **On-shell branch** (4084-4188): walk every vertex. For each final leg call `get_apx_fnrule(id, avg_q+mass, onshell=True)` (4103); for the mother/propagator leg of each non-final vertex call `get_apx_fnrule(id, q_total, onshell=False)` (4124); for the initial leg of the LAST vertex call `get_apx_fnrule(id, |M|, onshell=True)` (4128).
- **Off-shell branch** (4192-4266): a quick next-level estimate that treats all legs as on-shell with `avg_E = M/(n_final+1)` (4201), uses `est=True` propagators (rough), and applies `q_i = mass_i/2` in lorentz structures (4234).
- **Final correction** (4270): `apx_m *= 1/spin(initial)` — averages over the initial particle's spin states.

## Coupling / Lorentz strength (4132-4162)
Per vertex: `lorentz_factor = Σ_couplings |coupling|^2 * lor_value^2` (4160). The UFO Lorentz `structure` string is rewritten by a regex (`self.lor_pattern.sub(self.simplify_lorentz, ...)`, 4153) into something evaluable with the `q_dict_lor` energy substitutions, then `eval`-ed (4156). Form factors are inlined (4149-4151). If the evaluated value is 0, signs are flipped (`-`→`+`) and re-eval'd to dodge accidental cancellations (4157-4159). So the estimator uses REAL UFO couplings (run to scale; see decay-model page) and a crude scalarized Lorentz numerator.

## get_apx_fnrule (4274) — the "approximated Feynman rule" library
Per-leg propagator + numerator factor, keyed on `part.get('spin')` (MadGraph spin = 2S+1).
- **Propagator** (4284-4294): on-shell → `1.`; off-shell exact → `1/((q^2-m^2)^2 + m^2*apx_decaywidth^2)` (Breit-Wigner-squared, WIDTH IN THE DENOMINATOR via the particle's own `apx_decaywidth`, 4288-4289); off-shell `est=True` → rough `1/(0.5*max(q,m)^2)^2` (4293-4294) to avoid the resonance blow-up when q≈m.
- **Spin numerators** (multiply the propagator factor):
  - vector (spin 3): on-shell massive `*(1+(q/m)^2)`, massless `*1`; off-shell `*(1-2(q/m)^2+(q/m)^4)` (4298-4308).
  - fermion (spin 2): on-shell `*2q`, off-shell `*q^2` (4310-4314).
  - spin-3/2 (spin 4) and spin-2 (spin 5): explicit massive/massless formulas (4316-4352).
  - scalar (spin 1): nothing (returns the bare propagator/1) (4355).

## color_multiplicity_def (DecayModel, 1894) — hardcoded color table
`color_dict` (1915-1935) maps a sorted tuple of final-state color reps → list of `(mother_color, multiplicity)`. Two-body keys: (1,1),(1,3),(1,8),(1,6),(3,3),(3,6),(3,8),(6,6),(6,8),(8,8); plus four 3-body "quick reference" keys (3,3,8),(1,3,8),(1,3,3),(3,8,8). MadGraph color codes: 1=singlet, 3=(anti)triplet, 6=sextet, 8=octet. Example multiplicities: (3,3)→[(1,3),(8,0.5),(3,1),(6,1)]; (8,8)→[(1,8)]; (1,8)→[(8,0.5)].
- `Channel.get_color_multiplicity` (4358) recurses by popping two colors at a time, combining via the table, until the final color matches the initial particle's color (4375-4404). `base=True` (top call) returns 1 + a `logger.warning("Color structure ... is not included!")` if no table entry matches (4399-4401); intermediate recursion returns 0 on no-match. A `KeyError` from `color_multiplicity_def` (unlisted tuple) falls back to the recursion (4185-4188).
- In get_apx_matrixelement_sq the color factor only fires if any final color ≠ 1 (4166).

## get_apx_decaywidth_nextlevel (4496) — the error-estimate numerator
For each non-stable final leg with `(M - Σm_now + 2body_massdiff) > 0` (4523), adds a term approximating the width the leg's own two-body decay would contribute at the next level (4524-4533), built from that leg's `apx_decaywidth`, `c_psarea`, and ratios of `get_apx_fnrule` evaluations. `nextlevel = apx_decaywidth * Σ(err)` (4527). `estimate_width_error` (437) divides the summed nextlevel widths by `apx_decaywidth` to get `apx_decaywidth_err`, the float-body_decay loop's stop input (see channel-enumeration page).

## Cautions
- **This is an order-of-magnitude guess, not a width.** Equal-energy-sharing (avg_q), scalarized Lorentz numerators, hardcoded color table, the `c_psarea` PS fudge (decay_objects.py:3324). Its ONLY job is to decide enumeration depth (how many body-levels) and to prune channels below min_br. The physical width is the MadEvent survey (compute-widths-flow page). Never quote `apx_decaywidth` / `apx_matrixelement_sq` as a partial width.
- Color table is finite (the two-body + three-body tuples enumerated at 1915-1935 — read the set there). An exotic-color final state not in the table → `logger.warning` "Color structure ... is not included!" and multiplicity 1 (under-/mis-counted color factor in the ESTIMATE only — does not affect the survey).
- Off-shell channels are estimated as if on-shell (docstring 4070-4071); the off-shell branch is a coarse next-level proxy, deliberately not a real off-shell integral.
- The estimator uses running couplings at the decaying particle's mass (couplings are eval'd from globals populated by running_externals/internals — see decay-model-setup-stable-particles page), so a particle below the running low-mass cutoff (running_externals early-return, decay_objects.py:1963 — read the literal there) uses unrun pole couplings.
