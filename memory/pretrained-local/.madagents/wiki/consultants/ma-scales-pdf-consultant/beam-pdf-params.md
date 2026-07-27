---
description: LO run_card beam/PDF parameters (lpp1/2, pdlabel triple, lhaid, heavy-ion, lep densities) — defaults, allowed values, file:line cites in banner.py RunCardLO.default_setup.
---

# Beam / PDF parameters (RunCardLO.default_setup)

Source: `$MADGRAPH_INSTALL/madgraph/various/banner.py`, `RunCardLO.default_setup` (def at :4208).

## Beams (lpp / ebeam)
- `lpp1` (:4219) default read at :4219, `fortran_name=lpp(1)`, allowed `[-1,1,0,2,3,9,-2,-3,4,-4]`.
  shortcuts `{p:1, p~:-1, e-:3, e+:-3, mu-:4, mu+:-4, no:0}`.
  Comment semantics: 0=fixed energy, 1=PDF of proton, -1=PDF of antiproton, 2=elastic photon from proton, ±3=PDF of e-/e+, ±4=PDF of mu-/mu+, 9=PLUGIN.
- `lpp2` (:4222) identical to lpp1.
- `ebeam1`/`ebeam2` (:4225-4226) default read at :4225-4226 (per-beam energy in GeV; read fresh — do NOT assume a specific √s, the default has been an LHC-era value but is version-drifting), `fortran_name=ebeam(1/2)`.
- `polbeam1`/`polbeam2` (:4227-4230) default read at :4227-4230, hidden, NO `allowed=` list (range −100..+100 is comment-only, NOT parse-enforced; comment "--use lpp=0 for this parameter--"). The "use lpp=0" comment is INCOMPLETE/misleading: code allows polbeam for lepton beams too (rejects only |lpp|∈{1,2}, see below), so it IS meaningful for dressed leptons lpp=±3/±4, not just lpp=0.
  Runtime (`Template/LO/Source/setrun.f` :87-124): TWO different pol mappings depending on pdlabel:
  - NON-EVA path (:92,:99): `pol(i)=sign(1+|pb_i|/100, pb_i)` — encodes a polarization magnitude+sign for the helicity-amplitude machinery.
  - EVA path (:111-124): if `pdlabel=='eva'` (or per-beam `pdsublabel(i)=='eva'`), `pol(i) = (-1/200)*pb_i + 0.5` — maps polbeam −100/0/+100 → fLpol 1.0(pure LH)/0.5(unpol)/0.0(pure RH). This is the EXACT fLpol fed to `eva_get_pdf_by_PID` (eva-flux-driver-internals.md), NOT the sign() form.
  Beam polarization is REJECTED with `stop 1` "proton/anti-proton beam polarization are not allowed" if `|lpp|∈{1,2}` (hadron/elastic-photon-from-proton) (:89-90, :96-97). So polbeam is meaningful only for lepton beams (lpp ±3/±4) or fixed beams (lpp 0).

## NLO cross-class: DIS beam-config restriction (RunCardNLO ONLY)
`RunCardNLO.check_validity` (:5761) carries a beam-type gate ABSENT from RunCardLO:
- DIS reject (:5775-5777): `if (abs(lpp1)!=1 or abs(lpp2)!=1) and (lpp1==1 or lpp2==1): raise InvalidRunCard("Process like Deep Inelastic scattering not supported at NLO accuracy.")`. Boolean = "at least one beam not |proton| AND at least one beam is EXACTLY proton (lpp==1, signed)". So proton×lepton, proton×photon, proton×fixed all rejected at NLO. Note inner test is `lpp==1` not `abs(lpp)==1` → proton×antiproton (1,-1) does NOT trigger (both abs==1, outer False anyway). CONFIRMED doc claim exact.
- Lepton-lepton PDF override (:5779-5795): if not photon-photon (2,2), and if |lpp1|==|lpp2|∈{3,4} (dressed leptons) pdlabel must be a lep_density or 'emela' else InvalidRunCard (:5783-5784); otherwise (incl. lpp 0×0) pdlabel force-reset to `nn23nlo` + reweight_pdf off with an info log (:5786-5795).
- LO has NO DIS check: `RunCardLO.check_validity` (:4494) handles mixed beams via the pdlabel auto-correct/`mixed` path (:4585-4612) — LO accepts proton×lepton etc. This is a sharp RunCardLO-vs-RunCardNLO class divergence: pin the class before saying a beam config is legal.

## Heavy ion (hidden)
- `nb_proton1/2` (:4231,:4234) default read at :4231,:4234, allowed `[1,0,82,'*']`, shortcut `{lead:82}`.
- `nb_neutron1/2` (:4237,:4240) default read at :4237,:4240, allowed `[1,0,126,'*']`, shortcut `{lead:126}`.
- `mass_ion1/2` (:4243,:4247) default read at :4243,:4247, allowed `[-1,0,0.938, 207.9766521*0.938, 0.000511, 0.105,'*']`,
  shortcut `{proton:0.938, lead:207.9766521*0.938, electron:0.000511, muon:0.105}`.
- check_validity (:4615-4620): heavy-ion (nb_proton≠1 or nb_neutron≠0) only allowed when `lpp∈[1,2]`, else `InvalidRunCard`.

## PDF triple
- `valid_pdf` (:4251) = `['lhapdf','cteq6_m','cteq6_l','cteq6l1','nn23lo','nn23lo1','nn23nlo','iww','eva','edff','chff','none','mixed']` + `sum(allowed_lep_densities.values(),[])`.
- `pdlabel` (:4253) default read at :4253, hidden, allowed=valid_pdf.
- `pdlabel1` (:4254) `fortran_name=pdsublabel(1)`; `pdlabel2` (:4255) `pdsublabel(2)`; both default read at :4254-4255.
- `lhaid` (:4256) default read at :4256, hidden, NO inline comment in source. TRAP — do NOT read the PDF identity off the `lhaid` default: `lhaid` is consumed ONLY in `pdlabel=='lhapdf'` mode (`get_pdf_id` :3840-3845; run_card.dat:51 comment "if pdlabel=lhapdf, this is the lhapdf number"). In the DEFAULT bundled `pdlabel` mode the bundled-grid path (`Template/LO/Source/PDF/pdfwrap.f:252-255`) loads the grid keyed by the pdlabel STRING (nn23lo1 → `NNPDF23_lo_as_0130_qed_mem0.grid`, a grid whose αs(MZ)=0.130), and `lhaid` is IGNORED. So the EFFECTIVE default LO PDF is the nn23lo1 bundled grid (αs=0.130), NOT whatever set the `lhaid` number names in `pdfsets.index` (which can even be an NLO-labelled set). The number-vs-active-grid distinction is the trap: read the `lhaid` default fresh at :4256 and remember it is inert unless pdlabel=='lhapdf'.
- `get_pdf_id` written-banner pdfsup table (banner.py :3849-3851, NON-lhapdf branch): `cteq6_m:10000, cteq6_l:10041, cteq6l1:10042, nn23lo:246800, nn23lo1:247000, nn23nlo:244800` (none:0/iww:0/eva:0/edff:0/chff:0). These are the pdfsup1/2 values WRITTEN to the banner for bookkeeping when pdlabel≠lhapdf — distinct from the `lhaid` param default (read at :4256) which is the lhapdf-mode id. These pdfsup numbers are LHAPDF-catalog identifiers of named sets (identity facts, not MG defaults): `247000=NNPDF23_lo_as_0130_qed, 244800=NNPDF23_nlo_as_0119_qed, 246800=NNPDF23_lo_as_0119_qed`.

NOTE: `'emela'` is referenced by PDLabelBlock (:4068) and is valid at NLO (:5648) but is NOT in the LO `valid_pdf` static list (:4251) and is NOT a lep-density dir name — so `emela` is not a valid LO pdlabel.

NOTE: `'dressed'` is a RUNTIME pdlabel branch in pdg2pdf.f (:99) for dressed-lepton ISR but is likewise NOT in the LO `valid_pdf` static list — it is set indirectly via the lep-density/ISR machinery, not user-typed as `pdlabel='dressed'`. (`get_pdfup` in setrun.f does list 'dressed' in its name table, mapping it to LHAPDF id 00000.)

## `set` special-shortcut macros (beam/scale configs)
Source: `$MADGRAPH_INSTALL/madgraph/interface/common_run_interface.py`, `special_shortcut` dict (:5212-5225). These are `set <name> [VALUE]` REPL macros that expand to multiple `run_card` assignments — NOT run_card params themselves. Beam/scale ones (my slice):
- `pbpb` (:5223): lead-lead → `lpp1 1, lpp2 1, nb_proton1/2 82, nb_neutron1/2 126, mass_ion1/2 195.0820996698`. (195.0820996698 = 207.9766521×0.938, the Pb-208 A_amu × m_p convention — literal, not symbolic.) Help "setup heavy ion configuration for lead-lead collision" (:5241). NOTE: the token is lowercase `pbpb`, invoked as `set pbpb` — there is NO run_card `PbPb` shortcut.
- `pbp` (:5222): lead-proton → sets `nb_proton1 82, nb_neutron1 126, mass_ion1 195.08...` for beam1 and `nb_proton2 1, nb_neutron2 0` for beam2, BUT the last token is `run_card mass_ion1 -1` — a copy-paste BUG that RESETS mass_ion1 back to -1 (should be mass_ion2). Net effect: after `set pbp`, beam1 has nb_proton1=82 but mass_ion1=-1 → kinematic beam mass falls back to 0.938 (proton) while PDF x-scales per-82-nucleon. Exactly the decoupled/inconsistent ion setup beam-mass-stot.md warns about, shipped in the macro. Verify/patch mass_ion1 manually after `set pbp`.
- `pp` (:5224): reset to proton-proton → `nb_proton1/2 1, nb_neutron1/2 0, mass_ion1/2 -1`.
- `lhc VALUE` (TeV) (:5215): `lpp1/2 1, ebeam1/2 = VALUE*1000/2`. `lcc VALUE` (:5218) identical.
- `lep VALUE` / `ilc VALUE` (GeV) (:5216-5217): `lpp1/2 0` (NO PDF), `ebeam1/2 = VALUE/2`.
- `ebeam VALUE` (:5213): both ebeam. `lpp VALUE` (:5214): both lpp.
- `fixed_scale VALUE` (:5219): `fixed_fac_scale T, fixed_ren_scale T, scale VALUE, dsqrt_q2fact1/2 VALUE` — one-shot all-fixed-scales setter.
- `no_parton_cut` (:5220): `nocut T`. `cm_velocity VALUE` (:5221): sets √s for a given incoming velocity (lambda `set_CM_velocity`).
The macro INFRASTRUCTURE (special_shortcut mechanism) is ma-interface's; the beam/scale macro VALUES/semantics above are mine.

## Unknown-pdlabel handling (parse enforcement)
`pdlabel`/`pdlabel1`/`pdlabel2` carry `allowed=valid_pdf`. An out-of-list value (e.g. `nn31nlo`, `CT18NLO`) hits `RunCard.__setitem__` allowed-check (:1286-1308): `valid=False` → emits WARNING "value 'X' for entry 'pdlabel' is not valid. Preserving previous value: 'nn23lo1'." and REVERTS to the prior/default value (nn23lo1); does NOT raise under normal read (raiseerror=False). So an invented pdlabel does NOT "silently fall back" — it warns and reverts to default (parser-vs-fortran-mismatch flavor-2). There is no shorthand for NNPDF3.0/3.1/CT18/MSHT20; those require `pdlabel=lhapdf` + the matching `lhaid`.

## Lepton densities (discovered at runtime)
- `allowed_lep_densities` populated by `RunCard.get_lepton_densities` (:2809) from dir
  `$MADGRAPH_INSTALL/Template/Common/Source/PDF/lep_densities/` (MG5DIR mode) or `MEDIR/Source/PDF/lep_densities` (MADEVENT mode).
- Each subdir = one entry; identity read from `info` file `identity:` line, default `(-11,11)` (e+e-) if absent (:2822-2826).
- The available entries are DISCOVERED at runtime (version-dependent) — do not cache the list: read the subdirs of `$MADGRAPH_INSTALL/Template/Common/Source/PDF/lep_densities/` for the current install, and each subdir's `info` `identity:` line for its beam PIDs. Most collider dirs default to e+e- `(-11,11)`; a muon-collider dir carries `identity: -13,13`.
