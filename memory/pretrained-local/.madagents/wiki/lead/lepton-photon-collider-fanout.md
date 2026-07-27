---
description: The beams are not both protons. Leptons, photons, an asymmetric ep, polarized beams, or heavy ions.
---

# Lepton & photon collider — fan-out and owner map

The input-state (non-hadronic beam) axis. A "set up an e+e- / muon / photon / ep collider" request is almost entirely one slice's run_card surface (`ma-scales-pdf-consultant`), with exactly one cross-slice seam: the NLO-only DIS beam gate (`ma-amcatnlo-consultant`). Route the beam/flux/polarization/heavy-ion knobs to scales-pdf; route the "why does my mixed-beam config die at NLO but not LO" question to the LO-vs-NLO class split.

Complement of `pdf-and-scale-configuration-fanout.md` (that page is the *hadronic*-beam PDF/scale fan; this one is the non-hadronic beam-type fan). Both anchor on scales-pdf.

## Owner map (route each sub-question here)

- **All `lpp` beam-type + flux/PDF selection** → **ma-scales-pdf-consultant** (anchor). `lpp1`/`lpp2` values and meaning, the `pdlabel` auto-correction per beam type, per-beam `pdlabel1`/`pdlabel2`, ISR/EVA/EPA/dressed-lepton flux modes, `ebeam1`/`ebeam2`. Its `beam-pdf-params` page carries the full table.
- **Beam polarization** → **ma-scales-pdf-consultant** (`polbeam1`/`polbeam2`, `beam_pol` RunBlock, the `setrun.f` enforcement). This is *beam* polarization (a run_card knob); do NOT route here for *process-line* helicity/polarization tags `{T,L,R,…}` — those are `ma-polarization-consultant`.
- **Heavy-ion / UPC beams** → **ma-scales-pdf-consultant** (`nb_proton1/2`, `nb_neutron1/2`, `mass_ion1/2`, `ion_pdf` RunBlock).
- **The NLO DIS beam gate** → **ma-amcatnlo-consultant**. The one guard that rejects a mixed proton×non-proton beam config *at NLO only* (`RunCardNLO.check_validity`). Its `nlo-beam-dis-block` page carries the boolean.
- **LO-vs-NLO run_card class divergence generally** → see `runcard-lo-nlo-value-divergence.md` (the DIS gate is a sharp instance: present in RunCardNLO, absent from RunCardLO).

## Dispatch order

scales-pdf first — it owns essentially the whole beam surface and its return tells you whether the spec even reaches NLO. Engage amcatnlo second, and *only* when the spec is NLO (`[QCD]`/`[QED]`) with a mixed beam (a proton paired with anything non-proton), to confirm the DIS gate fires. A pure LO lepton/photon setup collapses to scales-pdf alone.

## The LO-accepts / NLO-rejects split (the load-bearing seam)

A mixed-beam config that parses and launches fine at **LO** is **hard-rejected at NLO**. Pin the run-card class before declaring any mixed-beam config legal:

- The gate lives in `RunCardNLO.check_validity` only; `RunCardLO` has no such check, so LO accepts *every* beam combination.
- It fires iff **(a)** at least one beam has `abs(lpp)!=1` (non-proton/antiproton) **AND (b)** at least one beam has `lpp==1` (proton, *signed*).
- **Asymmetric in proton vs antiproton:** proton (`lpp==1`) × non-proton is blocked; the same non-proton × **antiproton** (`lpp=-1`) **passes** — e.g. `lpp1=0,lpp2=-1` (lepton×antiproton) is legal at NLO. "Proton-paired-with-non-proton" is the right mental model only if "proton" means `lpp==1` exactly.
- Error is raised at **launch** (run_card validation on read), not at `generate`/`output`. Under `consistency='warning'` (a banner reload) the raise is downgraded to a `logger.warning`.

## Doc-myth traps (common write-ups get these wrong; the corrected fact is in the consultant page cited)

- **`lpp=±3/±4` is NOT simply "ISR structure functions".** The auto-default pdlabel for dressed leptons is **`eva`** (EVA = effective-vector-approximation, EW-boson γ/Z/W content), a *different* physics object from genuine photon-ISR (the `lep_densities`: isronlyll/isrbetll/…) and from LHAPDF lepton PDFs (`emela`, NLO-only). Three distinct paths; "ISR" conflates them. → scales-pdf `beam-pdf-params`.
- **`lpp=±2` default flux is `edff`, not generic "EPA".** `edff` = elastic dipole form-factor (gammaUPC); the classic EPA/IWW flux is the separate `iww` label; `chff` is the charge form-factor variant. → scales-pdf `beam-pdf-params`.
- **Beam polarization is NOT "only meaningful for lpp=0".** `polbeam1/2` applies to dressed leptons `lpp=±3/±4` too (mapped to `fLpol` for EVA); it is *blocked* (a `setrun.f` `stop 1`) only for `abs(lpp)∈{1,2}` (proton/EPA). The run_card comment "use lpp=0 for this parameter" is incomplete. Range −100..+100 is comment-only, not parse-enforced (no `allowed=` list). → scales-pdf `beam-pdf-params`.
- **Heavy-ion mode is only supported for `lpp∈{1,2}`.** Setting `nb_proton/nb_neutron` off their defaults with any other lpp raises InvalidRunCard. → scales-pdf.
- **EPA-EPA at NLO is a SUPPORTED mode, not a "passes validation but fails later" case.** `lpp1==lpp2==2` at NLO has dedicated handling (factorization scale forced fixed, dedicated runtime branch) — it is intended-accommodated. Whether a *specific* EPA/lepton NLO run converges at integration is a genuine open runtime question (probe-candidate), but passing the DIS gate is not a sign of an unsupported-but-slipped-through config. → amcatnlo `nlo-beam-dis-block`.

## Return-interpretation hint

If a scales-pdf return says a mixed-beam config is "fine", check whether it was reasoning about LO or NLO — the DIS gate makes the same config legal at LO and illegal at NLO. A "works at LO" is not evidence it works at NLO for any beam pair involving exactly one proton.
